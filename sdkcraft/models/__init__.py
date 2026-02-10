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
"""Data models for SDKcraft."""

from .constraints import Endpoint, ProjectName
from .linter import LinterIssue, LinterResult
from .located import Location
from .marked import MarkedLoader
from .marked_project import MarkedProject
from .metadata import Metadata
from .project import (
    CameraPlug,
    DesktopPlug,
    GPUPlug,
    MountPlug,
    MountSlot,
    Part,
    Plug,
    Plugs,
    Project,
    Slot,
    Slots,
    SSHPlug,
    TunnelPlug,
    TunnelSlot,
)

__all__ = [
    "CameraPlug",
    "DesktopPlug",
    "Endpoint",
    "GPUPlug",
    "LinterIssue",
    "LinterResult",
    "Location",
    "MarkedLoader",
    "MarkedProject",
    "Metadata",
    "MountPlug",
    "MountSlot",
    "Part",
    "Plug",
    "Plugs",
    "Project",
    "ProjectName",
    "Slot",
    "Slots",
    "SSHPlug",
    "TunnelPlug",
    "TunnelSlot",
]
