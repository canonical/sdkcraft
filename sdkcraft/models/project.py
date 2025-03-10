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
from typing import Annotated, Any

import craft_parts
import pydantic
from craft_application import models
from craft_application.models import (
    ProjectName,
)

from sdkcraft.errors import SdkcraftError


class MountPlug(models.CraftBaseModel):
    """Sdkcraft project mount plug definition."""

    interface: str
    workshop_target: str
    read_only: bool


class MountSlot(models.CraftBaseModel):
    """Sdkcraft project mount slot definition."""

    interface: str
    workshop_source: str


def _validate_part(item: dict[str, Any]) -> dict[str, Any]:
    """Verify each part (craft-parts will re-validate this)."""
    craft_parts.validate_part(item)
    if item.get("stage-packages") is not None:
        raise NotImplementedError(
            '"stage-packages" are not supported by sdkcraft. Consider using "setup-base" hook to install packages required by your SDK'
        )

    if item.get("stage-snaps") is not None:
        raise NotImplementedError(
            '"stage-snaps" are not supported by sdkcraft. Consider using "setup-base" hook to install snaps required by your SDK'
        )

    return item


def _validate_readonly(plug_name: str, plug: MountPlug | dict[str, Any]) -> None:
    # Accept either boolean or string "true"/"false"
    read_only = plug.get("read-only") if isinstance(plug, dict) else plug.read_only
    if isinstance(read_only, str):
        read_only = read_only.lower()
    allowed_values = {"true", "false", True, False, None}
    if read_only not in allowed_values:
        raise SdkcraftError(
            message=f"Value '{read_only}' in optional parameter 'read-only' for MountPlug '{plug_name}' is invalid. Must be one of: '\"true\"', '\"false\"', 'true', 'false'"
        )


class Project(models.Project):
    """Sdkcraft project definition."""

    plugs: dict[str, MountPlug | Any] | None
    slots: dict[str, MountSlot | Any] | None
    parts: dict[
        str,
        Annotated[dict[str, Any], pydantic.BeforeValidator(_validate_part)],
    ]

    @pydantic.field_validator("name")
    @classmethod
    def _validate_project_name(cls, name: ProjectName) -> ProjectName:
        if name == "agent":
            raise SdkcraftError(
                message=f"'{name}' is a reserved SDK name, please choose another name."
            )
        return name

    @pydantic.field_validator("plugs")
    @classmethod
    def _validate_plugs(
        cls, plugs: dict[str, MountPlug | Any] | None
    ) -> dict[str, MountPlug | Any] | None:
        if plugs is not None:
            for plug_name, plug in plugs.items():
                if (
                    isinstance(plug, dict)
                    and plug.get("interface") == "mount"  # pyright: ignore[reportUnknownMemberType]
                    and not plug.get("workshop-target")  # pyright: ignore[reportUnknownMemberType]
                ):
                    raise SdkcraftError(
                        message=f"MountPlug '{plug_name}' must have a 'workshop-target' parameter."
                    )

                if isinstance(plug, list):
                    raise SdkcraftError(message=f"Plug '{plug_name}' cannot be a list.")

                _validate_readonly(plug_name, plug)  # pyright: ignore[reportUnknownArgumentType]

        return plugs

    @pydantic.field_validator("slots")
    @classmethod
    def _validate_slots(
        cls, slots: dict[str, MountSlot | Any] | None
    ) -> dict[str, MountPlug | Any] | None:
        if slots is not None:
            for slot_name, slot in slots.items():
                if (
                    isinstance(slot, dict)
                    and slot.get("interface") == "mount"  # pyright: ignore[reportUnknownMemberType]
                    and (
                        not slot.get("workshop-source")  # pyright: ignore[reportUnknownMemberType]
                        or not isinstance(slot.get("workshop-source"), str)  # pyright: ignore[reportUnknownMemberType]
                    )
                ):
                    raise SdkcraftError(
                        message=f"MountSlot '{slot_name}' must have a 'workshop-source' string parameter."
                    )

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
