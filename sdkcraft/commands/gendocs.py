# Copyright 2024 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Generate documentation for SDKcraft."""

import textwrap
from argparse import Namespace
from typing import override

from craft_application.commands import AppCommand
from craft_cli import emit
from craft_cli.dispatcher import (
    _CustomArgumentParser,  # type: ignore[reportPrivateUsage]
)
from craft_cli.helptexts import OutputFormat


class GendocsCommand(AppCommand):
    """Generate documentation for SDKcraft."""

    name = "gendocs"
    help_msg = "Generate documentation"
    overview = textwrap.dedent(
        """
        Generate documentation for SDKcraft projects.
        """
    )

    @override
    def run(self, parsed_args: Namespace) -> None:
        """Run the command."""
        # Import here to avoid circular import
        from sdkcraft import cli

        # Create app instance to access command groups and dispatcher
        app = cli._create_app()  # noqa: SLF001 # type: ignore[reportPrivateUsage]
        dispatcher = app._create_dispatcher()  # noqa: SLF001 # type: ignore[reportPrivateUsage]
        help_builder = dispatcher._help_builder  # noqa: SLF001 # type: ignore[reportPrivateUsage]

        # Iterate through command groups and print markdown help for all commands
        for group in app.command_groups:
            emit.message(f"\n# {group.name} Commands\n")

            for cmd_class in sorted(group.commands, key=lambda c: c.name):
                cmd = cmd_class(app.app_config)
                parser = _CustomArgumentParser(help_builder)
                cmd.fill_parser(parser)

                # Collect arguments as (name, help) tuples
                arguments = []
                for action in parser._actions:  # noqa: SLF001
                    if action.dest == "help":
                        continue
                    name = (
                        ", ".join(action.option_strings)
                        if action.option_strings
                        else action.dest
                    )
                    arguments.append((name, action.help or ""))

                # Use craft-cli's built-in markdown help generation
                help_text = help_builder.get_command_help(
                    cmd, arguments, OutputFormat.markdown
                )
                emit.message(help_text)
