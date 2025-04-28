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
from typing import Annotated, Any, Literal, Protocol, TypeGuard, runtime_checkable

import craft_parts
from craft_application import models
from pydantic import AfterValidator, BeforeValidator, Field

from sdkcraft.models.constraints import Endpoint, ProjectName


class CameraPlug(models.CraftBaseModel):
    """Sdkcraft project camera plug definition."""

    interface: Literal["camera"]

    def validate_policy(self, name: str) -> None:
        """Check plug name."""
        if name != "camera":
            raise ValueError("camera interface plugs must be named 'camera'")


class DesktopPlug(models.CraftBaseModel):
    """Sdkcraft project desktop plug definition."""

    interface: Literal["desktop"]

    def validate_policy(self, name: str) -> None:
        """Check plug name."""
        if name != "desktop":
            raise ValueError("desktop interface plugs must be named 'desktop'")


class GPUPlug(models.CraftBaseModel):
    """Sdkcraft project GPU plug definition."""

    interface: Literal["gpu"]

    def validate_policy(self, name: str) -> None:
        """Check plug name."""
        if name != "gpu":
            raise ValueError("gpu interface plugs must be named 'gpu'")


class MountPlug(models.CraftBaseModel):
    """Sdkcraft project mount plug definition."""

    interface: Literal["mount"]
    workshop_target: str
    read_only: bool = False


class MountSlot(models.CraftBaseModel):
    """Sdkcraft project mount slot definition."""

    interface: Literal["mount"]
    workshop_source: str


class SSHPlug(models.CraftBaseModel):
    """Sdkcraft project SSH plug definition."""

    interface: Literal["ssh"]

    def validate_policy(self, name: str) -> None:
        """Check plug name."""
        if name != "ssh":
            raise ValueError("ssh interface plugs must be named 'ssh'")


class TunnelPlug(models.CraftBaseModel):
    """Sdkcraft project tunnel plug definition."""

    interface: Literal["tunnel"]
    endpoint: Endpoint = ""


class TunnelSlot(models.CraftBaseModel):
    """Sdkcraft project tunnel plug definition."""

    interface: Literal["tunnel"]
    endpoint: Endpoint = ""


Plug = Annotated[
    CameraPlug | DesktopPlug | GPUPlug | MountPlug | SSHPlug | TunnelPlug,
    Field(discriminator="interface"),
]
Slot = Annotated[
    MountSlot | TunnelSlot,
    Field(discriminator="interface"),
]


def _is_dict(items: Any) -> TypeGuard[dict[Any, Any]]:  # noqa: ANN401
    # Avoid pyright's reportUnknownVariableType and also mypy's redundant-cast.
    return isinstance(items, dict)


def _implicit_interface(name: Any, item: Any) -> Any:  # noqa: ANN401
    if item is None:
        return {"interface": name}
    if isinstance(item, str):
        return {"interface": str(item)}
    return item


def _implicit_interfaces(items: Any) -> Any:  # noqa: ANN401
    if not _is_dict(items):
        return items

    return {name: _implicit_interface(name, item) for name, item in items.items()}


@runtime_checkable
class PolicyValidator(Protocol):
    """Protocol for plugs or slots with specific interface policies."""

    def validate_policy(self, name: str) -> None:
        """Raise ValueError if the plug or slot violates policies."""


def _plug_policies(plugs: dict[str, Plug]) -> dict[str, Plug]:
    for name, plug in plugs.items():
        if isinstance(plug, PolicyValidator):
            plug.validate_policy(name)
    return plugs


def _slot_policies(slots: dict[str, Slot]) -> dict[str, Slot]:
    for name, slot in slots.items():
        if isinstance(slot, PolicyValidator):
            slot.validate_policy(name)
    return slots


Plugs = Annotated[
    dict[str, Plug],
    BeforeValidator(_implicit_interfaces),
    AfterValidator(_plug_policies),
]
Slots = Annotated[
    dict[str, Slot],
    BeforeValidator(_implicit_interfaces),
    AfterValidator(_slot_policies),
]


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
            "'stage-packages' are not supported by SDKcraft. Consider using 'setup-base' hook to install packages required by your SDK"
        )

    if item.get("stage-snaps") is not None:
        raise ValueError(
            "'stage-snaps' are not supported by SDKcraft. Consider using 'setup-base' hook to install snaps required by your SDK"
        )

    return item


Part = Annotated[BasePart, AfterValidator(_after_validate_part)]


DEFAULT_PART = {"default-part": {"plugin": "nil"}}


class Project(models.Project):
    """Sdkcraft project definition."""

    name: ProjectName

    plugs: Plugs = {}
    slots: Slots = {}
    parts: dict[str, Part] = DEFAULT_PART


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
