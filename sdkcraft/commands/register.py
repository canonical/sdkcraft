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

"""SDKcraft register command."""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, override

from craft_application.commands import AppCommand
from craft_cli import emit

from sdkcraft import store

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


class RegisterCommand(AppCommand):
    """Command to register an SDK name in the store."""

    name = "register"
    help_msg = "Register an SDK name in the store"
    overview = textwrap.dedent(
        """
        Register an SDK name in the SDK Store.

        This reserves the SDK name for your account, allowing you to upload
        revisions under that name. SDK names must be registered before uploading.
        """
    )

    @override
    def fill_parser(self, parser: ArgumentParser) -> None:
        """Add arguments specific to the register command."""
        parser.add_argument(
            "sdk_name",
            metavar="SDK",
            type=str,
            help="Name of the SDK to register",
        )

    @override
    def run(self, parsed_args: Namespace) -> None:
        """Run the register command."""
        sdk_name: str = parsed_args.sdk_name

        # Register via store client
        client = store.get_client()
        client.register_name(sdk_name)

        emit.message(f"Successfully registered SDK name: {sdk_name}")
