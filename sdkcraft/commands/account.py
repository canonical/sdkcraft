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
from pathlib import Path
from typing import TYPE_CHECKING, override

from craft_application.commands import AppCommand
from craft_cli import emit
from craft_store.errors import (
    CredentialsAlreadyAvailable,
    CredentialsUnavailable,
    UbuntuOneOtpRequiredError,
)

from sdkcraft import store
from sdkcraft.errors import SdkcraftError

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


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

        If `--export <file>` is used, the credentials are written to that file
        instead of being stored in the local keyring, and nothing is persisted
        locally. This is suitable for CI/CD environments:

            export {store.constants.ENVIRONMENT_STORE_CREDENTIALS}=$(cat <file>)
        """
    )
    examples: list[tuple[str, str]] = [
        ("Log in interactively", "sdkcraft login"),
        ("Export credentials for CI", "sdkcraft login --export credentials.txt"),
    ]
    related_commands: list[str] | None = None

    @override
    def fill_parser(self, parser: ArgumentParser) -> None:
        """Add own parameters to the general parser."""
        parser.add_argument(
            "--export",
            type=Path,
            help="Export the SDK Store credentials to a file instead of the local keyring",
        )

    @override
    def run(self, parsed_args: Namespace) -> None:
        """Run the command."""
        export_path: Path | None = parsed_args.export

        email = emit.prompt("Email address: ")
        password = emit.prompt("Password: ", hide=True)

        try:
            try:
                credentials = store.StoreClientCLI(
                    ephemeral=bool(export_path), use_environment_auth=False
                ).login(email=email, password=password)
            except UbuntuOneOtpRequiredError:
                otp = emit.prompt("One-time password: ")
                credentials = store.StoreClientCLI(
                    ephemeral=bool(export_path), use_environment_auth=False
                ).login(email=email, password=password, otp=otp)
        except CredentialsAlreadyAvailable as error:
            raise SdkcraftError(
                "Cannot log in because credentials were already found on this system "
                "(they may be from an older version of sdkcraft and no longer valid).",
                resolution="Run 'sdkcraft logout' first, then try again.",
            ) from error

        if export_path:
            export_path.write_text(credentials)
            emit.message(f"Login successful. Credentials exported to {str(export_path)!r}.")
        else:
            emit.message("Login successful")


class StoreLogoutCommand(AppCommand):
    """Command to clear SDK Store credentials."""

    name = "logout"
    help_msg = "Clear SDK Store credentials"
    overview = textwrap.dedent(
        """
        Clear the locally stored SDK Store credentials.

        This is required after upgrading from a version of sdkcraft that
        used a different login mechanism, before running `sdkcraft login`
        again.

        See also `sdkcraft whoami` to verify that you are logged in,
        and `sdkcraft login`.
        """
    )
    examples: list[tuple[str, str]] = [
        ("Log out", "sdkcraft logout"),
    ]
    related_commands: list[str] | None = None

    @override
    def run(self, parsed_args: Namespace) -> None:
        """Run the command."""
        try:
            store.get_client(use_environment_auth=False).logout()
        except CredentialsUnavailable:
            emit.message("You are not logged in.")
            return

        emit.message("Credentials cleared.")


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
