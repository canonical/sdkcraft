#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
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

"""Generate documentation for SDKcraft CLI."""

import sys
from pathlib import Path

from craft_cli import EmitterMode, emit
from craft_cli.dispatcher import _CustomArgumentParser
from craft_cli.helptexts import OutputFormat
from sdkcraft import cli


def generate_docs(output_dir: Path) -> None:
    """Generate CLI reference documentation."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create app instance to access command groups and dispatcher
    app = cli._create_app()  # noqa: SLF001
    dispatcher = app._create_dispatcher()  # noqa: SLF001
    help_builder = dispatcher._help_builder  # noqa: SLF001

    # Collect all commands
    cmd_classes = [
        cmd_class
        for group in app.command_groups
        for cmd_class in sorted(group.commands, key=lambda c: c.name)
    ]

    # Generate documentation for each command
    command_files = []
    for cmd_class in cmd_classes:
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
        help_text = help_builder.get_command_help(cmd, arguments, OutputFormat.markdown)

        # Add top-level header with command name
        command_section = f"# sdkcraft {cmd.name}\n\n{help_text}\n"

        # Generate individual file for this command
        individual_filename = f"sdkcraft-{cmd.name}.md"
        individual_path = output_dir / individual_filename
        individual_content = f"{command_section}\n"
        individual_path.write_text(individual_content)
        emit.message(f"Generated {individual_path}")
        command_files.append((cmd.name, individual_filename))

    # Generate index.md with links to individual files (sorted alphabetically)
    command_files.sort(key=lambda x: x[0])
    index_content = _generate_index(command_files)
    index_path = output_dir / "index.md"
    index_path.write_text(index_content)
    emit.message(f"Generated {index_path}")


def _generate_index(command_files: list[tuple[str, str]]) -> str:
    """Generate index.md with links to individual command files."""
    lines = [
        "```{eval-rst}",
        ".. meta::",
        "   :description: Overview of the 'sdkcraft' CLI utility, listing available",
        "                 commands and global options for managing SDKcraft projects.",
        "```",
        "",
        "# sdkcraft (CLI)",
        "",
        "The `sdkcraft` utility exposes the following commands,",
        "each with its own set of options,",
        "and also has a number of global flags:",
        "",
        "## Global Options",
        "",
        "`-h, --help`",
        "",
        "Print the help message for the command.",
        "",
        "## Commands",
        "",
    ]

    for cmd_name, filename in command_files:
        lines.append(f"- [sdkcraft {cmd_name}]({filename})")

    lines.extend(
        [
            "",
            "```{toctree}",
            ":hidden:",
            "",
        ]
    )

    for _cmd_name, filename in command_files:
        # Remove .md extension for toctree entries
        lines.append(filename.replace(".md", ""))

    lines.append("```")

    return "\n".join(lines)


if __name__ == "__main__":
    EXPECTED_ARGS = 2
    if len(sys.argv) != EXPECTED_ARGS:
        emit.init(EmitterMode.BRIEF, "gendocs", "gendocs", log_filepath=None)
        emit.error("Usage: gendocs.py <output_directory>")
        sys.exit(1)

    # Initialize emitter before generating docs
    emit.init(
        EmitterMode.BRIEF,
        "gendocs",
        "Starting documentation generation",
        log_filepath=None,
    )

    output_directory = Path(sys.argv[1])
    generate_docs(output_directory)
