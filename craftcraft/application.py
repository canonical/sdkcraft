#  This file is part of craftcraft.
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
"""Main application class for craftcraft."""
import copy
from typing import Any

import craft_parts
from craft_application import Application, AppMetadata, util

from craftcraft import models

APP_METADATA = AppMetadata(
    name="craftcraft",
    summary="Craft a craft application with craft-application",
    ProjectClass=models.Project,
)


class Craftcraft(Application):
    """Craftcraft application definition."""

    def configure(self, global_args: dict[str, Any]) -> None:
        """Configure the application using global command-line arguments."""

    def _configure_services(self, platform: str | None, build_for: str | None) -> None:
        if build_for is None:
            build_for = util.get_host_architecture()

        self.services.set_kwargs(
            "package",
            platform=platform,
            build_for=build_for,
        )
        super()._configure_services(platform, build_for)

    def _extra_yaml_transform(self, yaml_data: dict[str, Any]) -> dict[str, Any]:
        """Transform the YAML file before parsing it as a project."""
        yaml_data = copy.deepcopy(yaml_data)

        # Put your transforms here.
        yaml_data.update({})

        return yaml_data

    def _project_vars(self, yaml_data: dict[str, Any]) -> dict[str, str]:
        """Populate any variables to be used in the project info."""
        project_vars = super()._project_vars(yaml_data)

        # Update the dictionary here.
        project_vars.update({})

        return project_vars

    def _set_global_environment(self, info: craft_parts.ProjectInfo) -> None:
        """Populate the global environment to use when running the parts lifecycle."""
        super()._set_global_environment(info)
