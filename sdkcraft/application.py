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

from craft_application import Application, AppMetadata, commands
from craft_cli import Dispatcher
from typing_extensions import override

from sdkcraft import models

APP_METADATA = AppMetadata(
    name="sdkcraft",
    summary="Design and build SDKs with SDKcraft",
    docs_url="https://canonical-workshop.readthedocs-hosted.com/{version}",
    source_ignore_patterns=["*.sdk"],
    ProjectClass=models.Project,
)


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
            docs_base_url=self.app.versioned_docs_url,
            default_command=commands.lifecycle.PackCommand,
        )
