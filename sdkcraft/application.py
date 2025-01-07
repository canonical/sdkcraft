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
from craft_application import Application, AppMetadata, commands
from craft_cli import Dispatcher
from typing_extensions import override

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

    @override
    def _create_dispatcher(self) -> Dispatcher:
        """Overridden to set the default command to "pack"."""
        return Dispatcher(
            self.app.name,
            self.command_groups,
            summary=str(self.app.summary),
            extra_global_args=self._global_arguments,
            default_command=commands.lifecycle.PackCommand,
        )

    def set_defaults(self, yaml_data: dict[str, Any]) -> None:
        """Apply the expected default parts to a project if it doesn't contain any."""
        if 'parts' not in yaml_data:  # Only operate if there aren't any parts.
            yaml_data["parts"] = {'dummy': {'plugin': 'nil'}}
        if 'slots' not in yaml_data:
            yaml_data["slots"] = None
        if 'plugs' not in yaml_data:
            yaml_data["plugs"] = None
        if 'title' not in yaml_data:
            yaml_data["title"] = None
        if 'contact' not in yaml_data:
            yaml_data["contact"] = None
        if 'source-code' not in yaml_data:
            yaml_data["source-code"] = None
        if 'issues' not in yaml_data:
            yaml_data["issues"] = None

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
        self.set_defaults(yaml_data)

        return yaml_data

    def _set_global_environment(self, info: craft_parts.ProjectInfo) -> None:
        """Populate the global environment to use when running the parts lifecycle."""
        super()._set_global_environment(info)
