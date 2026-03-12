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

"""Tests for create-track command."""

from __future__ import annotations

from argparse import Namespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from craft_application.errors import CraftValidationError
from sdkcraft.commands.create_track import StoreCreateTrackCommand

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
    client.create_tracks.return_value = 1
    return mocker.patch(
        "sdkcraft.commands.create_track.store.get_client",
        return_value=client,
    )


########################
# Create Track Command #
########################


def test_create_track_single(
    app_config: dict[str, Any],
    fake_store_client: MockType,
    emitter: RecordingEmitter,
):
    cmd = StoreCreateTrackCommand(app_config)
    cmd.run(Namespace(sdk_name="go", tracks=["1.26"]))

    fake_store_client.return_value.create_tracks.assert_called_once_with("go", ["1.26"])
    emitter.assert_message("Created track: 1.26")
    emitter.assert_message('Successfully created 1 track(s) for "go" SDK')


def test_create_track_multiple(
    app_config: dict[str, Any],
    fake_store_client: MockType,
    emitter: RecordingEmitter,
):
    fake_store_client.return_value.create_tracks.return_value = 2

    cmd = StoreCreateTrackCommand(app_config)
    cmd.run(Namespace(sdk_name="go", tracks=["1.26", "1.25"]))

    fake_store_client.return_value.create_tracks.assert_called_once_with(
        "go", ["1.26", "1.25"]
    )
    emitter.assert_message("Created track: 1.26")
    emitter.assert_message("Created track: 1.25")
    emitter.assert_message('Successfully created 2 track(s) for "go" SDK')


def test_create_track_invalid_name(
    app_config: dict[str, Any],
    fake_store_client: MockType,
):
    cmd = StoreCreateTrackCommand(app_config)

    with pytest.raises(CraftValidationError):
        cmd.run(Namespace(sdk_name="go", tracks=["invalid--name"]))

    fake_store_client.return_value.create_tracks.assert_not_called()


def test_create_track_name_too_long(
    app_config: dict[str, Any],
    fake_store_client: MockType,
):
    cmd = StoreCreateTrackCommand(app_config)

    with pytest.raises(CraftValidationError):
        cmd.run(Namespace(sdk_name="go", tracks=["a" * 29]))

    fake_store_client.return_value.create_tracks.assert_not_called()
