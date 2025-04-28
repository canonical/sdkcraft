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

"""Creation of minimalist SDKcraft projects."""

import textwrap
from argparse import Namespace
from pathlib import Path

from craft_application.commands import AppCommand
from craft_cli import emit
from overrides import override  # pyright: ignore[reportUnknownVariableType]

from sdkcraft import errors


def init(sdkcraft_yaml_content: str) -> None:
    """Initialize an SDKcraft project.

    :param sdkcraft_yaml_content: Content of the sdk.yaml file
    :raises SdkcraftInitError: raises initialization error in case of conflicts
    with existing sdk.yaml files
    """
    sdk_yaml_path = Path("sdk.yaml")
    dot_sdk_yaml_path = sdk_yaml_path.with_name(".sdk.yaml")

    if sdk_yaml_path.is_file():
        raise errors.SdkcraftInitError(sdk_yaml_path)
    if dot_sdk_yaml_path.is_file():
        raise errors.SdkcraftInitError(dot_sdk_yaml_path)

    sdk_yaml_path.parent.mkdir(exist_ok=True)

    sdk_yaml_path.write_text(sdkcraft_yaml_content)

    emit.progress(f"Created {sdk_yaml_path}.")


class InitCommand(AppCommand):
    """Initialize an SDKcraft project."""

    name = "init"
    help_msg = "Initialize an SDKcraft project"
    overview = textwrap.dedent(
        """
        Initialize an SDKcraft project by creating a minimalist,
        yet functional, sdk.yaml file in the current directory.
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
    def run(self, parsed_args: Namespace) -> None:  # noqa: ARG002
        """Run the command."""
        init(self._INIT_TEMPLATE_YAML)
