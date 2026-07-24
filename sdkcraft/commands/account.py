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
from craft_store.errors import UbuntuOneOtpRequiredError

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

        Sdkcraft will prompt for your Ubuntu One email address and password
        (and a one-time password, if two-factor authentication is enabled).

        The login command requires a working keyring on the system it is used on.
        As an alternative, export {store.constants.ENVIRONMENT_STORE_CREDENTIALS!r}
        with the exported credentials.
        """
    )
    examples: list[tuple[str, str]] = [
        ("Log in interactively", "sdkcraft login"),
    ]
    related_commands: list[str] | None = None

    @override
    def run(self, parsed_args: Namespace) -> None:
        """Run the command."""
        email = emit.prompt("Email address: ")
        password = emit.prompt("Password: ", hide=True)

        try:
            store.StoreClientCLI().login(email=email, password=password)
        except UbuntuOneOtpRequiredError:
            otp = emit.prompt("One-time password: ")
            store.StoreClientCLI().login(email=email, password=password, otp=otp)

        emit.message("Login successful")


class StoreWhoamiCommand(AppCommand):
    """Command to display authentication status."""

    name = "whoami"
    help_msg = "Display login information"
    overview = textwrap.dedent(
        """
        Display information about the currently authenticated user.
        """
    )
    examples: list[tuple[str, str]] = [
        ("Show current login", "sdkcraft whoami"),
    ]
    related_commands: list[str] | None = None

    @override
    def run(self, parsed_args: Namespace) -> None:
        """Run the command."""
        client = store.get_client()

        try:
            data = client.whoami()

            account = data.get("account", {})
            email = account.get("email", "Unknown")
            username = account.get("username", "Unknown")
            account_id = account.get("id", "Unknown")

            emit.message(f"email: {email}")
            emit.message(f"username: {username}")
            emit.message(f"id: {account_id}")

            permissions = data.get("permissions")
            if permissions:
                emit.message(f"permissions: {', '.join(permissions)}")
            else:
                emit.message("permissions: no restrictions")

            channels = data.get("channels")
            if channels:
                emit.message(f"channels: {', '.join(channels)}")
            else:
                emit.message("channels: no restrictions")

            storage_info = client.get_credentials_storage_info()
            emit.message(f"token: {storage_info}")
        except Exception as error:
            emit.message(f"Not authenticated or authentication failed: {error}")
            raise
