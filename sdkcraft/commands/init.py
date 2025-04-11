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

"""Creation of minimalist sdkcraft projects."""

import textwrap
from pathlib import Path
from typing import TYPE_CHECKING

from craft_application.commands import AppCommand
from craft_cli import emit
from overrides import override  # pyright: ignore[reportUnknownVariableType]

from sdkcraft import errors

if TYPE_CHECKING:
    import argparse


def init(sdkcraft_yaml_content: str) -> None:
    """Initialize a sdkcraft project.

    :param sdkcraft_yaml_content: Content of the sdkcraft.yaml file
    :raises sdkcraftInitError: raises initialization error in case of conflicts
    with existing sdkcraft.yaml files
    """
    sdkcraft_yaml_path = Path("sdkcraft.yaml")

    if sdkcraft_yaml_path.is_file():
        raise errors.SdkcraftInitError(f"{sdkcraft_yaml_path}")

    if Path(f".{sdkcraft_yaml_path.name}").is_file():
        raise errors.SdkcraftInitError(f".{sdkcraft_yaml_path}")

    sdkcraft_yaml_path.parent.mkdir(exist_ok=True)

    sdkcraft_yaml_path.write_text(sdkcraft_yaml_content)

    emit.progress(f"Created {sdkcraft_yaml_path}.")


class InitCommand(AppCommand):
    """Initialize a sdkcraft project."""

    name = "init"
    help_msg = "Initialize a sdkcraft project"
    overview = textwrap.dedent(
        """
        Initialize a sdkcraft project by creating a minimalist,
        yet functional, sdkcraft.yaml file in the current directory.
        """
    )

    _INIT_TEMPLATE_YAML = textwrap.dedent(
        """\
            name: my-sdk-name   # the name of your SDK
            base: ubuntu@22.04  # the base environment for this SDK
            version: '0.1'      # just for humans. Semantic versioning is recommended
            summary: Single-line elevator pitch for your amazing SDK    # 79 char long summary
            description: |
              This is my my-sdk-name's description. You have a paragraph or two to tell the
              most important story about it. Keep it under 100 words though,
              we live in tweetspace.
            license: GPL-3.0    # your SDK's SPDX license
            platforms:          # The platforms this SDK should be built on and run on
              amd64:

            parts:
              my-part:
                plugin: nil
            """
    )

    @override
    def run(self, parsed_args: "argparse.Namespace") -> None:  # noqa: ARG002
        """Run the command."""
        init(self._INIT_TEMPLATE_YAML)
