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

from pathlib import Path

from craft_application import Application, AppMetadata, commands
from craft_cli import Dispatcher
from typing_extensions import override

from sdkcraft import models

APP_METADATA = AppMetadata(
    name="sdkcraft",
    summary="Design and build SDKs with SDKcraft",
    ProjectClass=models.Project,
)

_PROJECT_FILES = [Path("sdk.yaml"), Path(".sdk.yaml"), Path("sdkcraft.yaml")]


class Sdkcraft(Application):
    """SDKcraft application definition."""

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

    @override
    def _resolve_project_path(self, project_dir: Path | None) -> Path:
        """Overridden to handle the three possible locations for sdk.yaml."""
        if project_dir is None:
            project_dir = self.project_dir

        for project_file in _PROJECT_FILES:
            try:
                return (project_dir / project_file).resolve(strict=True)
            except FileNotFoundError:  # noqa: PERF203
                pass

        # Retry to get the ideal error message.
        return (project_dir / _PROJECT_FILES[0]).resolve(strict=True)
