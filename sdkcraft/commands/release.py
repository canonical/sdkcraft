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

"""SDKcraft release command."""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, cast, override

from craft_application.commands import AppCommand
from craft_application.errors import CraftValidationError
from craft_cli import emit
from craft_store import models
from pydantic import TypeAdapter, ValidationError

from sdkcraft import store
from sdkcraft.errors import SdkcraftError
from sdkcraft.models.constraints import ChannelName
from sdkcraft.models.store import SdkChannelMapModel, SdkListReleasesModel

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


def _format_channel_map(channel_map: list[SdkChannelMapModel]) -> list[str]:
    """Render channel map entries as a plain aligned table."""
    col_channel = "CHANNEL"
    col_revision = "REVISION"

    rows = [(entry.channel, str(entry.revision)) for entry in channel_map]

    w_channel = (
        max(len(col_channel), *(len(r[0]) for r in rows)) if rows else len(col_channel)
    )
    w_revision = (
        max(len(col_revision), *(len(r[1]) for r in rows))
        if rows
        else len(col_revision)
    )

    lines = [f"{col_channel:<{w_channel}}  {col_revision:<{w_revision}}"]
    for ch, rev in rows:
        lines.append(f"{ch:<{w_channel}}  {rev:<{w_revision}}")
    return lines


class StoreReleaseCommand(AppCommand):
    """Command to release an SDK revision to store channels."""

    name = "release"
    help_msg = "Release an SDK revision to store channels"
    examples: list[tuple[str, str]] = [
        ("Release revision 8 to stable", "sdkcraft release my-sdk 8 stable"),
        (
            "Release revision 8 to latest/stable",
            "sdkcraft release my-sdk 8 latest/stable",
        ),
        (
            "Release revision 9 to multiple channels",
            "sdkcraft release my-sdk 9 beta,edge",
        ),
    ]
    overview = textwrap.dedent(
        """
        Release <sdk> at <revision> to the selected store <channels>.
        <channels> is a comma-separated list of valid channels on the store.

        The <revision> must exist on the store; to see available revisions,
        run `sdkcraft revisions <sdk>`.

        The channel map is displayed after the operation.

        The format for a channel is [<track>/]<risk>[/<branch>], where:

        - <track> is used to have long-term release channels.
        - <risk> can only be `stable`, `candidate`, `beta`, or `edge`.
        - <branch> is optional and dynamically creates a channel with
          a one-month expiration.
        """
    )

    @override
    def fill_parser(self, parser: ArgumentParser) -> None:
        """Add arguments specific to the release command."""
        parser.add_argument(
            "sdk",
            metavar="SDK",
            type=str,
            help="Name of the SDK to release",
        )
        parser.add_argument(
            "revision",
            metavar="REVISION",
            type=int,
            help="Revision number to release",
        )
        parser.add_argument(
            "channels",
            metavar="CHANNELS",
            type=str,
            help="Comma-separated list of channels to release to (e.g. latest/stable,edge)",
        )

    @override
    def run(self, parsed_args: Namespace) -> None:
        """Run the release command."""
        sdk_name: str = parsed_args.sdk
        revision: int = parsed_args.revision
        channels_str: str = parsed_args.channels

        channel_list = [c.strip() for c in channels_str.split(",") if c.strip()]
        if not channel_list:
            raise SdkcraftError("No channels specified.")

        for channel in channel_list:
            try:
                TypeAdapter(ChannelName).validate_python(channel)
            except ValidationError as exc:
                raise CraftValidationError.from_pydantic(exc) from exc

        client = store.get_client()

        release_request = [
            models.ReleaseRequestModel(channel=ch, revision=revision)
            for ch in channel_list
        ]
        client.release(name=sdk_name, release_request=release_request)

        result = cast(SdkListReleasesModel, client.get_list_releases(name=sdk_name))
        for line in _format_channel_map(result.channel_map):
            emit.message(line)
