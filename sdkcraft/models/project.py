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
"""Sdkcraft project definition.

This module defines a sdkcraft.yaml file, exportable to a JSON schema.
"""

import json
from pathlib import Path
from typing import Annotated, Any, Literal

import craft_parts
import pydantic
from craft_application import models
from pydantic import AfterValidator, BeforeValidator

from sdkcraft.models.constraints import ProjectName


class MountPlug(models.CraftBaseModel):
    """Sdkcraft project mount plug definition."""

    interface: Literal["mount"]
    workshop_target: str
    read_only: bool = False


class MountSlot(models.CraftBaseModel):
    """Sdkcraft project mount slot definition."""

    interface: Literal["mount"]
    workshop_source: str


# TODO: replace with models.Part after merging  # noqa: FIX002
# https://github.com/canonical/craft-application/pull/675
def _before_validate_part(part: Any) -> Any:  # noqa: ANN401
    craft_parts.validate_part(part)
    return part


BasePart = Annotated[dict[str, Any], BeforeValidator(_before_validate_part)]


def _after_validate_part(item: dict[str, Any]) -> dict[str, Any]:
    """Verify SDK-specific attributes for a part."""
    if item.get("stage-packages") is not None:
        raise ValueError(
            "'stage-packages' are not supported by sdkcraft. Consider using 'setup-base' hook to install packages required by your SDK"
        )

    if item.get("stage-snaps") is not None:
        raise ValueError(
            "'stage-snaps' are not supported by sdkcraft. Consider using 'setup-base' hook to install snaps required by your SDK"
        )

    return item


Part = Annotated[BasePart, AfterValidator(_after_validate_part)]


class Project(models.Project):
    """Sdkcraft project definition."""

    name: ProjectName

    plugs: dict[str, MountPlug | Any] | None
    slots: dict[str, MountSlot | Any] | None
    parts: dict[str, Part]

    @pydantic.field_validator("plugs")
    @classmethod
    def _validate_plugs(
        cls, plugs: dict[str, MountPlug | Any] | None
    ) -> dict[str, MountPlug | Any] | None:
        if plugs is not None:
            for plug_name, plug in plugs.items():
                if isinstance(plug, dict) and plug.get("interface") == "mount":  # pyright: ignore[reportUnknownMemberType]
                    plugs[plug_name] = MountPlug.unmarshal(plug)  # pyright: ignore[reportUnknownArgumentType]

        return plugs

    @pydantic.field_validator("slots")
    @classmethod
    def _validate_slots(
        cls, slots: dict[str, MountSlot | Any] | None
    ) -> dict[str, MountPlug | Any] | None:
        if slots is not None:
            for slot_name, slot in slots.items():
                if isinstance(slot, dict) and slot.get("interface") == "mount":  # pyright: ignore[reportUnknownMemberType]
                    slots[slot_name] = MountSlot.unmarshal(slot)  # pyright: ignore[reportUnknownArgumentType]

        return slots


def export_schema() -> None:
    """Sdkcraft project schema export.

    To run: PYTHONPATH=. python sdkcraft/models/project.py.
    """
    schema = Project.model_json_schema()
    with Path("schema.json").open("w") as file:
        json.dump(schema, file, indent=2)


if __name__ == "__main__":
    # Call the export function
    export_schema()
