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

"""SDKcraft Store Account management commands."""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, override

from craft_application.commands import AppCommand
from craft_cli import emit

from sdkcraft import store

if TYPE_CHECKING:
    from argparse import Namespace


class StoreLoginCommand(AppCommand):
    """Command to log in to the SDK Store."""

    name = "login"
    help_msg = "Log in to the SDK Store"
    overview = textwrap.dedent(
        f"""
        Log in to the SDK Store.

        The login command requires a working keyring on the system it is used on.
        As an alternative, export {store.constants.ENVIRONMENT_STORE_CREDENTIALS!r}
        with the exported credentials.
        """
    )

    @override
    def run(self, parsed_args: Namespace) -> None:
        """Run the command."""
        store.StoreClientCLI().login()

        emit.message("Login successful")
