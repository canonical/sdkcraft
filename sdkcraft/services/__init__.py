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
"""Services for SDKcraft."""

from craft_application import ServiceFactory

from .buildplan import BuildPlanService
from .package import PackageService
from .project import ProjectService


def register_sdkcraft_services() -> None:
    """Register SDKcraft-specific services."""
    ServiceFactory.register("build_plan", BuildPlanService)
    ServiceFactory.register("package", PackageService)
    ServiceFactory.register("project", ProjectService)


__all__ = [
    "BuildPlanService",
    "PackageService",
    "ProjectService",
    "register_sdkcraft_services",
]
