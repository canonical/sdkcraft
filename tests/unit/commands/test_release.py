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

"""Tests for the release command."""

from __future__ import annotations

from argparse import Namespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from craft_application.errors import CraftValidationError
from craft_store import models
from sdkcraft.commands.release import StoreReleaseCommand
from sdkcraft.models.store import SdkChannelMapModel

if TYPE_CHECKING:
    from craft_cli.pytest_plugin import RecordingEmitter
    from pytest_mock import MockerFixture, MockType


############
# Helpers  #
############

_CHANNEL_MAP_ENTRY = SdkChannelMapModel.unmarshal(
    {
        "base": {"architecture": "amd64", "channel": "all", "name": "all"},
        "channel": "latest/edge",
        "expiration-date": None,
        "revision": 8,
        "when": "2026-01-19T06:20:26Z",
    }
)


############
# Fixtures #
############


@pytest.fixture
def fake_store_client(mocker: MockerFixture) -> MockType:
    client = MagicMock()
    client.release.return_value = None
    list_releases_result = MagicMock()
    list_releases_result.channel_map = [_CHANNEL_MAP_ENTRY]
    client.get_list_releases.return_value = list_releases_result
    return mocker.patch("sdkcraft.store.get_client", return_value=client)


###################
# Release Command #
###################


def test_release_single_channel(
    app_config: dict[str, Any],
    fake_store_client: MockType,
) -> None:
    cmd = StoreReleaseCommand(app_config)
    cmd.run(Namespace(sdk="my-sdk", revision=8, channels="stable"))

    fake_store_client.return_value.release.assert_called_once_with(
        name="my-sdk",
        release_request=[models.ReleaseRequestModel(channel="stable", revision=8)],
    )


def test_release_multiple_channels(
    app_config: dict[str, Any],
    fake_store_client: MockType,
) -> None:
    cmd = StoreReleaseCommand(app_config)
    cmd.run(Namespace(sdk="my-sdk", revision=9, channels="beta,edge"))

    fake_store_client.return_value.release.assert_called_once_with(
        name="my-sdk",
        release_request=[
            models.ReleaseRequestModel(channel="beta", revision=9),
            models.ReleaseRequestModel(channel="edge", revision=9),
        ],
    )


def test_release_track_qualified_channel(
    app_config: dict[str, Any],
    fake_store_client: MockType,
) -> None:
    cmd = StoreReleaseCommand(app_config)
    cmd.run(Namespace(sdk="my-sdk", revision=9, channels="lts-channel/stable"))

    fake_store_client.return_value.release.assert_called_once_with(
        name="my-sdk",
        release_request=[
            models.ReleaseRequestModel(channel="lts-channel/stable", revision=9)
        ],
    )


def test_release_channel_with_branch(
    app_config: dict[str, Any],
    fake_store_client: MockType,
) -> None:
    cmd = StoreReleaseCommand(app_config)
    cmd.run(Namespace(sdk="my-sdk", revision=8, channels="stable/my-branch"))

    fake_store_client.return_value.release.assert_called_once_with(
        name="my-sdk",
        release_request=[
            models.ReleaseRequestModel(channel="stable/my-branch", revision=8)
        ],
    )


def test_release_invalid_risk(
    app_config: dict[str, Any],
    fake_store_client: MockType,
) -> None:
    cmd = StoreReleaseCommand(app_config)

    with pytest.raises(CraftValidationError, match="nightly"):
        cmd.run(Namespace(sdk="my-sdk", revision=9, channels="nightly"))

    fake_store_client.return_value.release.assert_not_called()


def test_release_invalid_risk_in_list(
    app_config: dict[str, Any],
    fake_store_client: MockType,
) -> None:
    cmd = StoreReleaseCommand(app_config)

    with pytest.raises(CraftValidationError, match="nightly"):
        cmd.run(Namespace(sdk="my-sdk", revision=9, channels="stable,nightly"))

    fake_store_client.return_value.release.assert_not_called()


def test_release_channel_map_displayed(
    app_config: dict[str, Any],
    fake_store_client: MockType,
    emitter: RecordingEmitter,
) -> None:
    cmd = StoreReleaseCommand(app_config)
    cmd.run(Namespace(sdk="my-sdk", revision=8, channels="edge"))

    # list_releases must be called to build the channel map
    fake_store_client.return_value.get_list_releases.assert_called_once_with(
        name="my-sdk"
    )

    # Header and each data row are emitted as separate messages.
    emitter.assert_message(r"CHANNEL.*REVISION.*", regex=True)
    emitter.assert_message(r"latest/edge.*8.*", regex=True)
