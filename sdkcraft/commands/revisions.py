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

"""SDKcraft revisions command."""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, cast, override

from craft_application.commands import AppCommand
from craft_cli import emit

from sdkcraft import store
from sdkcraft.commands._formatters import format_revisions
from sdkcraft.models.store import SdkListReleasesModel

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


class StoreRevisionsCommand(AppCommand):
    """Command to list SDK revisions available on the store."""

    name = "revisions"
    help_msg = "List SDK revisions available on the store"
    examples: list[tuple[str, str]] = [
        ("List revisions for an SDK", "sdkcraft revisions my-sdk"),
    ]
    overview = textwrap.dedent(
        """
        List all available channels and revisions for <sdk> from the store.

        Use this command to find the revision number to pass to
        `sdkcraft release <sdk> <revision> <channels>`.
        """
    )

    @override
    def fill_parser(self, parser: ArgumentParser) -> None:
        """Add arguments specific to the revisions command."""
        parser.add_argument(
            "sdk",
            metavar="SDK",
            type=str,
            help="Name of the SDK to list revisions for",
        )

    @override
    def run(self, parsed_args: Namespace) -> None:
        """Run the revisions command."""
        sdk_name: str = parsed_args.sdk

        client = store.get_client()
        result = cast(SdkListReleasesModel, client.get_list_releases(name=sdk_name))
        revisions = client.list_sdk_revisions(sdk_name)

        for line in format_revisions(revisions, result.channel_map):
            emit.message(line)
