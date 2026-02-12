#  This file is part of sdkcraft.
#
# Copyright 2024 Canonical Ltd.
#
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the GNU General Public License version 3, as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranties of MERCHANTABILITY,
#  SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Pydantic models which remember YAML metadata."""

from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, model_validator
from yaml import Mark, Node

from sdkcraft.models.marked import Marked


class Location(BaseModel):
    """Region of text within a file."""

    line: int | None = None
    end_line: int | None = None
    column: int | None = None
    end_column: int | None = None


class Located[T](BaseModel):
    """Holds a value together with line number information.

    Can be used when unmarshaling from a MarkedLoader.
    """

    value: T
    location: Location = Location()

    @model_validator(mode="before")
    @classmethod
    def _marked_to_located(cls, value: Any) -> Any:  # noqa: ANN401
        if not isinstance(value, Marked):
            return {"value": value}

        return {  # pyright: ignore[reportUnknownVariableType]
            "value": value.value,  # pyright: ignore[reportUnknownMemberType]
            "location": _node_location(value.node),
        }


def _node_location(node: Node) -> Location:
    location = Location()

    if isinstance(node.start_mark, Mark):
        location.line = node.start_mark.line + 1
        location.column = node.start_mark.column + 1

        if isinstance(node.end_mark, Mark):
            location.end_line = node.end_mark.line + 1
            location.end_column = node.end_mark.column

    return location


type Unmarked[T] = Annotated[T, BeforeValidator(Marked.unwrap)]
"""Tells Pydantic to ignore YAML metadata when unmarshaling.

Typically only required for primitive YAML types (datetime, str, etc.).
"""
