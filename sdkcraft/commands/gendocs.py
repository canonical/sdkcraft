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

"""Hidden command to generate CLI reference documentation."""

from __future__ import annotations

import importlib.resources
import textwrap
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast, override

from craft_application.commands import AppCommand
from craft_cli import emit
from gencodo import CommandGroup, TemplateInfo, gen_docs_tree

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace
    from collections.abc import Sequence

    import craft_cli
    from gencodo import Command


class GenerateDocsCommand(AppCommand):
    """Generate CLI reference documentation in reStructuredText."""

    name = "generate-docs"
    help_msg = "Generate CLI reference documentation"
    overview = textwrap.dedent(
        """
        Generate reStructuredText reference pages for every visible
        sdkcraft command, plus an index page.  The output is written
        to the given directory.
        """
    )
    hidden = True
    always_load_project = False
    examples: list[tuple[str, str]] = []
    related_commands: list[str] | None = None

    def __init__(self, config: dict[str, Any] | None) -> None:
        super().__init__(config)
        if config is not None:
            self._command_groups: list[craft_cli.CommandGroup] = config[
                "command_groups"
            ]

    @override
    def fill_parser(self, parser: ArgumentParser) -> None:
        """Add the output_dir positional argument."""
        parser.add_argument(
            "output_dir",
            type=Path,
            help="Directory to write generated .rst files into.",
        )

    @override
    def run(self, parsed_args: Namespace) -> None:
        """Run the command."""
        command_groups = [
            CommandGroup(
                name=g.name,
                commands=cast("Sequence[type[Command]]", g.commands),
            )
            for g in self._command_groups
            if not all(getattr(c, "hidden", False) for c in g.commands)
        ]

        templates = _load_templates()
        command_config: dict[str, Any] = {
            "app": self._app,
            "services": self._services,
        }

        generated = gen_docs_tree(
            appname="sdkcraft",
            command_groups=command_groups,
            output_dir=parsed_args.output_dir,
            templates=templates,
            file_extension=".rst",
            command_config=command_config,
        )

        emit.message(
            f"Generated {len(generated)} command pages in {parsed_args.output_dir}/:"
        )
        for filename in generated:
            emit.message(f"  {filename}")
        emit.message(f"  {templates.index_file_name}")


def _load_templates() -> TemplateInfo:
    """Load custom reST templates matching the Workshop documentation style."""
    templates_dir = importlib.resources.files("sdkcraft") / "templates"
    command_template = (templates_dir / "command.rst.j2").read_text(encoding="utf-8")
    index_template = (templates_dir / "index.rst.j2").read_text(encoding="utf-8")
    return TemplateInfo(
        index_file_name="sdkcraft.rst",
        index_template=index_template,
        command_template=command_template,
    )
