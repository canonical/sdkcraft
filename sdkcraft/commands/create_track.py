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

"""SDKcraft create-track command."""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, override

from craft_application.commands import AppCommand
from craft_application.errors import CraftValidationError
from craft_cli import emit
from pydantic import TypeAdapter, ValidationError

from sdkcraft import store
from sdkcraft.errors import SdkcraftError
from sdkcraft.models.constraints import TrackName

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


class StoreCreateTrackCommand(AppCommand):
    """Command to create tracks for an SDK on the SDK Store."""

    name = "create-track"
    help_msg = "Create one or more tracks for an SDK on the SDK Store"
    overview = textwrap.dedent(
        """
        Create one or more tracks for an SDK on the SDK Store.

        The command lists all tracks it created.
        Tracks must match an existing guardrail for this SDK.
        """
    )
    examples: list[tuple[str, str]] = [
        (
            'Create two tracks for the "go" SDK',
            "sdkcraft create-track --track 1.26 --track 1.25 go",
        ),
    ]

    @override
    def fill_parser(self, parser: ArgumentParser) -> None:
        """Add arguments specific to the create-track command."""
        parser.add_argument(
            "sdk_name",
            metavar="SDK",
            type=str,
            help="Name of the SDK to create a track for",
        )
        parser.add_argument(
            "--track",
            action="append",
            dest="tracks",
            required=True,
            help="The track name to create (can be repeated)",
        )

    @override
    def run(self, parsed_args: Namespace) -> None:
        """Run the create-track command."""
        sdk_name: str = parsed_args.sdk_name
        tracks: list[str] = parsed_args.tracks

        if not tracks:
            raise SdkcraftError("No tracks specified.")

        for track in tracks:
            try:
                TypeAdapter(TrackName).validate_python(track)
            except ValidationError as exc:
                raise CraftValidationError.from_pydantic(exc) from exc

        client = store.get_client()
        num_created = client.create_tracks(sdk_name, tracks)

        for track in tracks:
            emit.message(f"Created track: {track}")
        emit.message(
            f'Successfully created {num_created} track(s) for "{sdk_name}" SDK'
        )
