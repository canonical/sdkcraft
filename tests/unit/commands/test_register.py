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

"""Tests for register command."""

from __future__ import annotations

from argparse import Namespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from sdkcraft.commands.register import StoreRegisterCommand

if TYPE_CHECKING:
    from craft_cli.pytest_plugin import RecordingEmitter
    from pytest_mock import MockerFixture, MockType


############
# Fixtures #
############


@pytest.fixture
def fake_store_client(mocker: MockerFixture) -> MockType:
    """Mock store.get_client."""
    client = MagicMock()
    client.register_name.return_value = None
    return mocker.patch(
        "sdkcraft.store.get_client",
        return_value=client,
    )


####################
# Register Command #
####################


def test_register_success(
    app_config: dict[str, Any],
    fake_store_client: MockType,
    emitter: RecordingEmitter,
):
    """Test successful SDK registration."""
    cmd = StoreRegisterCommand(app_config)
    cmd.run(Namespace(sdk_name="my-awesome-sdk"))

    fake_store_client.return_value.register_name.assert_called_once_with(
        "my-awesome-sdk"
    )
    emitter.assert_message("Successfully registered SDK name: my-awesome-sdk")


def test_register_with_special_characters(
    app_config: dict,
    fake_store_client: MockType,
    emitter: RecordingEmitter,
):
    """Test registration with SDK name containing special characters."""
    cmd = StoreRegisterCommand(app_config)
    cmd.run(Namespace(sdk_name="my-sdk-2024"))

    fake_store_client.return_value.register_name.assert_called_once_with("my-sdk-2024")
    emitter.assert_message("Successfully registered SDK name: my-sdk-2024")
