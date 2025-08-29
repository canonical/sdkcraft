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
"""SDKcraft project definition.

This module defines an sdk.yaml file, exportable to a JSON schema.
"""

import json
from pathlib import Path
from string import Template
from typing import Annotated, Any, Literal, Protocol, TypeGuard, runtime_checkable

from craft_application import models
from craft_application.models import project
from pydantic import AfterValidator, BeforeValidator, Field

from sdkcraft.models.constraints import (
    FILE_MODE_MASK,
    CleanAbsPath,
    Endpoint,
    FileMode,
    PlugName,
    ProjectName,
    SlotName,
    UserGroupID,
)

WORKSHOP_UID_GID = 1000
ROOT_UMASK = 0o022
NORMAL_UMASK = 0o002


class CameraPlug(models.CraftBaseModel):
    """SDKcraft project camera plug definition."""

    interface: Literal["camera"]

    def validate_policy(self, name: str) -> None:
        """Check plug name."""
        if name != "camera":
            raise ValueError("camera interface plugs must be named 'camera'")


class DesktopPlug(models.CraftBaseModel):
    """SDKcraft project desktop plug definition."""

    interface: Literal["desktop"]

    def validate_policy(self, name: str) -> None:
        """Check plug name."""
        if name != "desktop":
            raise ValueError("desktop interface plugs must be named 'desktop'")


class GPUPlug(models.CraftBaseModel):
    """SDKcraft project GPU plug definition."""

    interface: Literal["gpu"]

    def validate_policy(self, name: str) -> None:
        """Check plug name."""
        if name != "gpu":
            raise ValueError("gpu interface plugs must be named 'gpu'")


def _default_uid_gid(plug: dict[str, Any]) -> int:
    path = plug.get("workshop_target", "")
    for prefix in ("/home/workshop", "/project", "/run/user/1000"):
        if path == prefix or path.startswith(prefix + "/"):
            return WORKSHOP_UID_GID
    return 0


def _default_mode(plug: dict[str, Any]) -> int:
    if plug.get("uid", WORKSHOP_UID_GID) == 0:
        return FILE_MODE_MASK & ~ROOT_UMASK
    return FILE_MODE_MASK & ~NORMAL_UMASK


class MountPlug(models.CraftBaseModel):
    """SDKcraft project mount plug definition."""

    interface: Literal["mount"]
    workshop_target: CleanAbsPath
    uid: UserGroupID = Field(default_factory=_default_uid_gid)
    gid: UserGroupID = Field(default_factory=_default_uid_gid)
    mode: FileMode = Field(default_factory=_default_mode)
    read_only: bool = False


def _expand_sdk(path: str) -> str:
    try:
        return Template(path).substitute({"SDK": "/var/lib/workshop/sdk/unknown"})
    except KeyError as e:
        key = next(iter(e.args), None)
        suffix = f"in {path!r}" if key is None else f"{key!r}"
        raise ValueError(f"unexpected variable {suffix}")


class MountSlot(models.CraftBaseModel):
    """SDKcraft project mount slot definition."""

    interface: Literal["mount"]
    workshop_source: Annotated[CleanAbsPath, BeforeValidator(_expand_sdk)]


class SSHPlug(models.CraftBaseModel):
    """SDKcraft project SSH plug definition."""

    interface: Literal["ssh"]

    def validate_policy(self, name: str) -> None:
        """Check plug name."""
        if name != "ssh":
            raise ValueError("ssh interface plugs must be named 'ssh'")


class TunnelPlug(models.CraftBaseModel):
    """SDKcraft project tunnel plug definition."""

    interface: Literal["tunnel"]
    endpoint: Endpoint = ""


class TunnelSlot(models.CraftBaseModel):
    """SDKcraft project tunnel plug definition."""

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
    dict[PlugName, Plug],
    BeforeValidator(_implicit_interfaces),
    AfterValidator(_plug_policies),
]
Slots = Annotated[
    dict[SlotName, Slot],
    BeforeValidator(_implicit_interfaces),
    AfterValidator(_slot_policies),
]


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


Part = Annotated[project.Part, AfterValidator(_after_validate_part)]


DEFAULT_PART = {"default-part": {"plugin": "nil"}}


class Project(models.Project):
    """SDKcraft project definition."""

    name: ProjectName

    plugs: Plugs = {}
    slots: Slots = {}
    parts: dict[str, Part] = DEFAULT_PART


def export_schema() -> None:
    """SDKcraft project schema export.

    To run: PYTHONPATH=. python sdkcraft/models/project.py.
    """
    schema = Project.model_json_schema()
    with Path("schema.json").open("w") as file:
        json.dump(schema, file, indent=2)


if __name__ == "__main__":
    # Call the export function
    export_schema()
