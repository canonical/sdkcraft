# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranties of MERCHANTABILITY,
# SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Tests for store account commands."""

from __future__ import annotations

from argparse import Namespace
from typing import TYPE_CHECKING, Any

import pytest
from sdkcraft.commands.account import StoreLoginCommand

if TYPE_CHECKING:
    from craft_cli.pytest_plugin import RecordingEmitter
    from pytest_mock import MockerFixture, MockType

############
# Fixtures #
############


@pytest.fixture
def fake_store_login(mocker: MockerFixture) -> MockType:
    """Mock StoreClientCLI login method."""
    return mocker.patch(
        "sdkcraft.store.StoreClientCLI.login",
        autospec=True,
        return_value="secret-credentials",
    )


#################
# Login Command #
#################


def test_login_calls_store_client(
    app_config: dict[str, Any], fake_store_login: MockType, emitter: RecordingEmitter
):
    """Test run() calls login on store client."""
    cmd = StoreLoginCommand(app_config)
    cmd.run(Namespace())

    fake_store_login.assert_called_once()
    emitter.assert_message("Login successful")
