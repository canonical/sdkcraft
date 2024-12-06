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

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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

class MountSlot(models.CraftBaseModel):
    """Sdkcraft project mount slot definition."""

    interface: str
    workshop_source: str

class Project(models.Project):
    """Sdkcraft project definition."""

    plugs: dict[str, MountPlug | Any] | None
    slots: dict[str, MountSlot | Any] | None
    parts: dict[str, dict[str, Any]]

    @pydantic.validator("name")
    def _validate_project_name(cls, name: ProjectName) -> ProjectName:
        if name == "agent":
            raise SdkcraftError(
                message=f"'{name}' is a reserved SDK name, please choose another name."
            )
        return name

    @pydantic.validator("parts", each_item=True)
    def _validate_parts(cls, item: dict[str, Any]) -> dict[str, Any]:
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

    @pydantic.validator("plugs")
    def _validate_plugs(
        cls, plugs: dict[str, MountPlug | Any]
    ) -> dict[str, MountPlug | Any]:
        if plugs is not None:
            for plug_name, plug in plugs.items():
                if (
                    isinstance(plug, dict)
                    and plug.get("interface") == "mount"
                    and not plug.get("workshop-target")
                ):
                    raise SdkcraftError(
                        message=f"MountPlug '{plug_name}' must have a 'workshop-target' parameter."
                    )

                if isinstance(plug, list):
                    raise SdkcraftError(message=f"Plug '{plug_name}' cannot be a list.")

        return plugs

    @pydantic.validator("slots")
    def _validate_slots(
        cls, slots: dict[str, MountSlot | Any]
    ) -> dict[str, MountPlug | Any]:
        if slots is not None:
            for slot_name, slot in slots.items():
                if (
                    isinstance(slot, dict)
                    and slot.get("interface") == "mount"
                    and (not slot.get("workshop-source") or not isinstance(slot.get("workshop-source"), str))
                ):
                    raise SdkcraftError(
                        message=f"MountSlot '{slot_name}' must have a 'workshop-source' string parameter.")

        return slots

def export_schema() -> None:
    """Sdkcraft project schema export.

    To run: PYTHONPATH=. python sdkcraft/models/project.py.
    """
    schema = Project.schema()
    with Path("schema.json").open("w") as file:
        json.dump(schema, file, indent=2)


if __name__ == "__main__":
    # Call the export function
    export_schema()
