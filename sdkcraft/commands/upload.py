# Copyright 2026 Canonical Ltd.
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

"""SDKcraft upload command."""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import TYPE_CHECKING, override

from craft_application.commands import AppCommand

from sdkcraft import errors, store

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


class UploadCommand(AppCommand):
    """Command to upload an SDK artifact to the store."""

    name = "upload"
    help_msg = "Upload an SDK artifact to the store"
    overview = textwrap.dedent(
        """
        Upload an SDK artifact to the SDK Store.

        The artifact must be a .sdk file created by the pack command.
        Optionally, the uploaded revision can be released to specified channels.
        """
    )

    @override
    def fill_parser(self, parser: ArgumentParser) -> None:
        """Add arguments specific to the upload command."""
        parser.add_argument(
            "sdk_file",
            metavar="SDK",
            type=Path,
            help="Path to the .sdk file to upload",
        )
        parser.add_argument(
            "--release",
            type=str,
            metavar="CHANNELS",
            help="Comma-separated list of channels to release to after upload",
        )

    @override
    def run(self, parsed_args: Namespace) -> None:
        """Run the upload command."""
        sdk_file: Path = parsed_args.sdk_file
        release_channels_str: str | None = parsed_args.release

        # Validate SDK file exists
        if not sdk_file.exists():
            raise errors.SdkcraftError(f"SDK file not found: {sdk_file}")

        # Validate SDK file extension
        if sdk_file.suffix != ".sdk":
            raise errors.SdkcraftError(f"File must have .sdk extension: {sdk_file}")

        # Parse release channels if provided
        release_channels = None
        if release_channels_str:
            release_channels = [
                ch.strip() for ch in release_channels_str.split(",") if ch.strip()
            ]

        # Upload via store client
        client = store.StoreClientCLI()
        client.upload(sdk_file=sdk_file, release_channels=release_channels)
