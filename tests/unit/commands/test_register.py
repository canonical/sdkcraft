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
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from craft_application import AppMetadata
from sdkcraft.commands.register import RegisterCommand
from sdkcraft.models import Project

if TYPE_CHECKING:
    from pytest_mock import MockerFixture, MockType


############
# Fixtures #
############


@pytest.fixture
def app_config(mocker: MockerFixture) -> dict:
    """Provide a minimal app config for command tests."""
    return {
        "app": AppMetadata(
            name="sdkcraft",
            summary="Test app",
            ProjectClass=Project,
        ),
        "services": mocker.MagicMock(),
    }


@pytest.fixture
def fake_store_client(mocker: MockerFixture) -> MockType:
    """Mock store.get_client."""
    client = MagicMock()
    client.register_name.return_value = None
    return mocker.patch(
        "sdkcraft.store.get_client",
        return_value=client,
    )


@pytest.fixture
def fake_emit(mocker: MockerFixture) -> MockType:
    """Mock emit module."""
    return mocker.patch("sdkcraft.commands.register.emit")


####################
# Register Command #
####################


def test_register_success(
    app_config: dict,
    fake_store_client: MockType,
    fake_emit: MockType,
):
    """Test successful SDK registration."""
    cmd = RegisterCommand(app_config)
    cmd.run(Namespace(sdk_name="my-awesome-sdk"))

    fake_store_client.return_value.register_name.assert_called_once_with(
        "my-awesome-sdk"
    )
    fake_emit.message.assert_called_once_with(
        "Successfully registered SDK name: my-awesome-sdk"
    )


def test_register_with_special_characters(
    app_config: dict,
    fake_store_client: MockType,
    fake_emit: MockType,
):
    """Test registration with SDK name containing special characters."""
    cmd = RegisterCommand(app_config)
    cmd.run(Namespace(sdk_name="my-sdk-2024"))

    fake_store_client.return_value.register_name.assert_called_once_with("my-sdk-2024")
    fake_emit.message.assert_called_once_with(
        "Successfully registered SDK name: my-sdk-2024"
    )
