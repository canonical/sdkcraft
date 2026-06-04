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
"""SDKcraft linting infrastructure."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal

from craft_application.models import CraftBaseModel
from pydantic import (
    BeforeValidator,
    ConfigDict,
    Discriminator,
)

from sdkcraft.models.located import Located, Unmarked
from sdkcraft.models.marked import Marked


class MarkedModel(CraftBaseModel):
    """More lenient base model for validating with line numbers."""

    model_config = ConfigDict(validate_assignment=False, extra="ignore")


class MountPlug(MarkedModel):
    """Marked project mount plug definition."""

    interface: Literal["mount"]
    workshop_target: Located[str]


class OtherPlug(MarkedModel):
    """Marked project generic plug definition."""

    interface: Literal[
        "camera", "custom-device", "desktop", "gpu", "ssh-agent", "tunnel"
    ]


type Plug = Annotated[MountPlug | OtherPlug, Discriminator("interface")]


class MountSlot(MarkedModel):
    """Marked project mount slot definition."""

    interface: Literal["mount"]
    workshop_source: Located[str]


class OtherSlot(MarkedModel):
    """Marked project generic plug definition."""

    interface: Literal["tunnel"]


type Slot = Annotated[MountSlot | OtherSlot, Discriminator("interface")]


def _implicit_interface(name: Any, value: Any) -> Any:  # noqa: ANN401
    value = Marked.unwrap(value)
    if value is None:
        return {"interface": Marked.unwrap(name)}
    if isinstance(value, str):
        return {"interface": value}
    if isinstance(value, dict):
        iface = value.get("interface")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        if iface is not None:
            value["interface"] = Marked.unwrap(iface)
    return value  # pyright: ignore[reportUnknownVariableType]


def _implicit_interfaces(value: Any) -> Any:  # noqa: ANN401
    if not isinstance(value, dict):
        return value

    return {k: _implicit_interface(k, v) for k, v in value.items()}  # pyright: ignore[reportUnknownVariableType]


type Plugs = Annotated[dict[Unmarked[str], Plug], BeforeValidator(_implicit_interfaces)]
type Slots = Annotated[dict[Unmarked[str], Slot], BeforeValidator(_implicit_interfaces)]


class MarkedProject(MarkedModel):
    """SDKcraft project definition marked with line numbers."""

    name: Unmarked[str]

    plugs: Plugs = {}
    slots: Slots = {}

    path: Path
    abspath: Path
