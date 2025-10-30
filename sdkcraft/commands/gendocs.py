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
from argparse import ArgumentParser, Namespace
from pathlib import Path
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
    hidden = True

    @override
    def fill_parser(self, parser: ArgumentParser) -> None:
        """Add arguments to the parser."""
        parser.add_argument(
            "directory",
            type=str,
            help="Output directory for generated documentation",
        )

    @override
    def run(self, parsed_args: Namespace) -> None:
        """Run the command."""
        # Import here to avoid circular import
        from sdkcraft import cli

        output_dir = Path(parsed_args.directory)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create app instance to access command groups and dispatcher
        app = cli._create_app()  # noqa: SLF001 # type: ignore[reportPrivateUsage]
        dispatcher = app._create_dispatcher()  # noqa: SLF001 # type: ignore[reportPrivateUsage]
        help_builder = dispatcher._help_builder  # noqa: SLF001 # type: ignore[reportPrivateUsage]

        # Collect all commands except gendocs
        all_commands = [
            (group, cmd_class)
            for group in app.command_groups
            for cmd_class in sorted(group.commands, key=lambda c: c.name)
            if cmd_class.name != "gendocs"
        ]

        # Generate sdkcraft.rst
        index_content = self._generate_index(all_commands)
        index_path = output_dir / "sdkcraft.rst"
        index_path.write_text(index_content)
        emit.message(f"Generated {index_path}")

        # Generate individual RST files for each command
        for _group, cmd_class in all_commands:
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

            # Write to individual file
            cmd_filename = f"sdkcraft-{cmd.name}.md"
            cmd_path = output_dir / cmd_filename
            cmd_path.write_text(help_text)
            emit.message(f"Generated {cmd_path}")

    def _generate_index(self, commands: list) -> str:
        """Generate sdkcraft.rst content."""
        lines = [
            ".. _ref_sdkcraft_cli:",
            "",
            ".. meta::",
            "   :description: Overview of the 'sdkcraft' CLI utility, listing available",
            "                 commands and global options for managing SDKcraft projects.",
            "",
            "sdkcraft (CLI)",
            "===============",
            "",
            ".. @artefact sdkcraft (CLI)",
            "",
            "The :program:`sdkcraft` utility exposes the following commands,",
            "each with its own set of options,",
            "and also has a number of global flags:",
            "",
            "-h, --help",
            "",
            "   Print the help message for the command.",
            "",
            "",
        ]

        # Add include directives for each command
        for _, cmd_class in commands:
            lines.append("")
            lines.append(f".. include:: sdkcraft-{cmd_class.name}.md")
            lines.append("")

        lines.append("")
        return "\n".join(lines)
