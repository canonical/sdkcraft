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
"""Main application class for sdkcraft."""

import copy
from typing import Any

import craft_parts
from craft_application import Application, AppMetadata

from sdkcraft import models

APP_METADATA = AppMetadata(
    name="sdkcraft",
    summary="Design and build SDKs with sdkcraft",
    ProjectClass=models.Project,
)


class Sdkcraft(Application):
    """sdkcraft application definition."""

    def configure(self, global_args: dict[str, Any]) -> None:
        """Configure the application using global command-line arguments."""

    def _extra_yaml_transform(
        self,
        yaml_data: dict[str, Any],
        *,
        build_on: str,  # noqa: ARG002 (Unused method argument)
        build_for: str | None,  # noqa: ARG002 (Unused method argument)
    ) -> dict[str, Any]:
        """Transform the YAML file before parsing it as a project."""
        yaml_data = copy.deepcopy(yaml_data)

        # Put your transforms here.
        yaml_data.update({})

        return yaml_data

    def _set_global_environment(self, info: craft_parts.ProjectInfo) -> None:
        """Populate the global environment to use when running the parts lifecycle."""
        super()._set_global_environment(info)
