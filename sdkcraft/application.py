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
from craft_cli.helptexts import HelpBuilder
from craft_parts.plugins.python_v2.python_plugin import PythonPlugin

from sdkcraft.commands import PackCommand
from sdkcraft.config import ConfigModel
from sdkcraft.models import Project

if TYPE_CHECKING:
    from craft_parts.plugins.plugins import PluginType

APP_METADATA = AppMetadata(
    name="sdkcraft",
    summary="Design and build SDKs with SDKcraft",
    docs_url="https://ubuntu.com/workshop/docs/",
    source_ignore_patterns=["*.sdk"],
    ProjectClass=Project,
    supports_multi_base=True,
    always_repack=False,
    ConfigModel=ConfigModel,
)


class _HelpBuilder(HelpBuilder):
    """Point command help URLs at the workshop docs layout.

    craft-cli links to ``/reference/commands/<name>``, but sdkcraft commands
    are documented as sections on a single page at
    ``/reference/cli/sdkcraft/#sdkcraft-<name>``.
    """

    @override
    def _build_plain_command_help(
        self, command: Any, *args: Any, **kwargs: Any
    ) -> list[str]:
        blocks = super()._build_plain_command_help(command, *args, **kwargs)
        wrong = f"/reference/commands/{command.name}"
        right = f"/reference/cli/sdkcraft/#sdkcraft-{command.name}"
        return [block.replace(wrong, right) for block in blocks]


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
        dispatcher = Dispatcher(
            self.app.name,
            self.command_groups,
            summary=str(self.app.summary),
            extra_global_args=self._global_arguments,
            docs_base_url=self.app.versioned_docs_url,
            default_command=PackCommand,
        )
        # Reuse the help builder craft-cli configured, only swapping in our URL
        # rewrite. Re-classing avoids re-instantiating HelpBuilder, whose
        # constructor signature/state may change; reconstruct only if that fails.
        help_builder = dispatcher._help_builder  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        try:
            help_builder.__class__ = _HelpBuilder
        except TypeError:
            dispatcher._help_builder = _HelpBuilder(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
                self.app.name,
                str(self.app.summary),
                self.command_groups,
                docs_base_url=self.app.versioned_docs_url,
            )
        return dispatcher

    @override
    def _get_app_plugins(self) -> dict[str, PluginType]:
        return {"python": PythonPlugin}
