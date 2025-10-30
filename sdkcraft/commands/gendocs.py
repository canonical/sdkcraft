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
from typing import Any, override

from craft_application.commands import AppCommand
from craft_cli import emit
from craft_cli.dispatcher import (
    _CustomArgumentParser,  # type: ignore[reportPrivateUsage]
)


class GendocsCommand(AppCommand):
    """Generate documentation for SDKcraft."""

    name = "gendocs"
    help_msg = "Generate documentation"
    overview = textwrap.dedent(
        """
        Generate documentation for SDKcraft projects.
        """
    )

    def _extract_command_info(
        self,
        cmd_class: Any,  # noqa: ANN401
        app: Any,  # noqa: ANN401
        help_builder: Any,  # noqa: ANN401
        global_options: dict[str, tuple[list[str], str]],
    ) -> tuple[
        AppCommand,
        dict[str, tuple[Any, Any]],
        list[tuple[str, Any, Any]],
    ]:
        """Extract command information including options and required arguments."""
        cmd = cmd_class(app.app_config)
        p = _CustomArgumentParser(help_builder)
        cmd.fill_parser(p)

        options = {}
        required = []

        # Separate options from required arguments
        for action in p._actions:  # noqa: SLF001
            if action.option_strings and action.dest not in global_options:
                options[action.dest] = (action.option_strings, action.help)
            elif (action.required or not action.option_strings) and (
                action.metavar or action.dest != "help"
            ):
                required.append((action.dest, action.metavar, action.help))  # type: ignore[reportUnknownMemberType]

        return cmd, options, required  # type: ignore[reportUnknownVariableType]

    @override
    def run(self, parsed_args: Namespace) -> None:  # noqa: PLR0912
        """Run the command."""
        # Import here to avoid circular import
        from sdkcraft import cli

        # Create app instance to access command groups and dispatcher
        app = cli._create_app()  # noqa: SLF001 # type: ignore[reportPrivateUsage]
        dispatcher = app._create_dispatcher()  # noqa: SLF001 # type: ignore[reportPrivateUsage]
        help_builder = dispatcher._help_builder  # noqa: SLF001 # type: ignore[reportPrivateUsage]

        # Collect global options
        global_options = {}
        for arg in dispatcher.global_arguments:
            opts = [x for x in [arg.short_option, arg.long_option] if x is not None]
            global_options[arg.name] = (opts, arg.help_message)

        # Iterate through command groups and print help
        for group in app.command_groups:
            emit.message(f"\n{group.name} Commands")
            emit.message("=" * (len(group.name) + 9))

            for cmd_class in sorted(group.commands, key=lambda c: c.name):
                cmd, options, required = self._extract_command_info(
                    cmd_class,
                    app,
                    help_builder,
                    global_options,  # type: ignore[reportUnknownArgumentType]
                )

                emit.message(f"\n{cmd.name}")
                emit.message("-" * len(cmd.name))
                emit.message(cmd.overview.strip())

                # Build usage string
                usage_parts = [f"sdkcraft {cmd.name}"]
                if options or global_options:
                    usage_parts.append("[options]")
                for _dest, metavar, _ in required:
                    arg_name = metavar if metavar else _dest
                    usage_parts.append(f"<{arg_name}>")

                emit.message(f"\nUsage: {' '.join(usage_parts)}")

                if required:
                    emit.message("\nRequired arguments:")
                    for _dest, metavar, help_text in required:
                        arg_name = metavar if metavar else _dest
                        emit.message(f"  <{arg_name}>")
                        if help_text and help_text != "==SUPPRESS==":
                            emit.message(f"    {help_text}")

                if options:
                    emit.message("\nOptions:")
                    for _dest, (names, help_text) in sorted(options.items()):
                        emit.message(f"  {', '.join(names)}")
                        if help_text and help_text != "==SUPPRESS==":
                            emit.message(f"    {help_text}")

        emit.message("\n\nGlobal Options")
        emit.message("=" * 14)
        for _dest, (names, help_text) in sorted(global_options.items()):  # type: ignore[reportUnknownArgumentType,reportUnknownVariableType]
            if names:
                emit.message(f"  {', '.join(names)}")  # type: ignore[reportUnknownArgumentType]
                if help_text and help_text != "==SUPPRESS==":
                    emit.message(f"    {help_text}")
