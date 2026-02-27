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

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from craft_application import Application, AppMetadata
from craft_cli import Dispatcher
from craft_parts.plugins.python_v2.python_plugin import PythonPlugin

from sdkcraft.commands import PackCommand
from sdkcraft.config import ConfigModel
from sdkcraft.models import Project

if TYPE_CHECKING:
    from craft_parts.plugins.plugins import PluginType

APP_METADATA = AppMetadata(
    name="sdkcraft",
    summary="Design and build SDKs with SDKcraft",
    docs_url="https://canonical-workshop.readthedocs-hosted.com/{version}",
    source_ignore_patterns=["*.sdk"],
    ProjectClass=Project,
    supports_multi_base=True,
    always_repack=False,
    ConfigModel=ConfigModel,
)


class Sdkcraft(Application):
    """SDKcraft application definition."""

    @property
    @override
    def app_config(self) -> dict[str, Any]:
        """Include command groups so hidden commands can discover siblings."""
        config = super().app_config
        config["command_groups"] = self.command_groups
        return config

    @override
    def _create_dispatcher(self) -> Dispatcher:
        """Overridden to set the default command to "pack"."""
        return Dispatcher(
            self.app.name,
            self.command_groups,
            summary=str(self.app.summary),
            extra_global_args=self._global_arguments,
            docs_base_url=self.app.versioned_docs_url,
            default_command=PackCommand,
        )

    @override
    def _get_app_plugins(self) -> dict[str, PluginType]:
        return {"python": PythonPlugin}
