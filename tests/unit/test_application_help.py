# This file is part of sdkcraft.
#
# Copyright 2024 Canonical Ltd.
#
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the GNU General Public License version 3, as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranties of MERCHANTABILITY,
#  SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Tests for CLI help text customisation."""

from __future__ import annotations

from craft_cli import BaseCommand, CommandGroup
from craft_cli.helptexts import OutputFormat
from sdkcraft.application import _HelpBuilder


class _LoginCommand(BaseCommand):
    name = "login"
    help_msg = "Log in to the SDK Store"
    overview = "Log in to the SDK Store"


def test_command_help_url_points_to_workshop_docs():
    """Command help links to the workshop docs layout, not craft-cli's default.

    Renders through the real craft-cli help builder so the test also fails if
    craft-cli changes its ``/reference/commands/<name>`` path and our rewrite
    silently stops matching.
    """
    builder = _HelpBuilder(
        "sdkcraft",
        "Design and build SDKs with SDKcraft",
        [CommandGroup("Account", [_LoginCommand])],
        docs_base_url="https://ubuntu.com/workshop/docs/",
    )

    help_text = builder.get_command_help(
        _LoginCommand(None),
        [("-h, --help", "Show this help message and exit")],
        OutputFormat.plain,
    )

    assert (
        "https://ubuntu.com/workshop/docs/reference/cli/sdkcraft/#sdkcraft-login"
        in help_text
    )
    assert "/reference/commands/login" not in help_text
