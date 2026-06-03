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

"""Tests for the revisions command."""

from __future__ import annotations

from argparse import Namespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from sdkcraft.commands.revisions import StoreRevisionsCommand
from sdkcraft.models.store import SdkChannelMapModel, SdkRevisionModel

if TYPE_CHECKING:
    from craft_cli.pytest_plugin import RecordingEmitter
    from pytest_mock import MockerFixture, MockType


############
# Helpers  #
############


def _channel_map_entry(
    channel: str,
    *,
    revision: int,
    architecture: str = "amd64",
) -> SdkChannelMapModel:
    return SdkChannelMapModel.unmarshal(
        {
            "base": {"architecture": architecture, "channel": "all", "name": "all"},
            "channel": channel,
            "expiration-date": None,
            "revision": revision,
            "when": "2026-01-19T06:20:26Z",
        }
    )


def _revision_entry(
    revision: int,
    *,
    created_at: str,
    architecture: str = "amd64",
) -> SdkRevisionModel:
    return SdkRevisionModel.unmarshal(
        {
            "bases": [
                {
                    "architecture": architecture,
                    "channel": "all",
                    "name": "all",
                }
            ],
            "created-at": created_at,
            "created-by": "CqyWllG7eo6hDoj2sMRtj6dFUtiU7DEK",
            "revision": revision,
            "sha3-384": "3ffbfe6ca0f4822f42ba57947b7a5e095b3df9e21e5ddd6b433ef7e0e08396c4c2bc5c75f21326d93d8efcdb26bf352c",
            "size": 59422629,
            "status": "released",
            "version": "1.24.6",
        }
    )


############
# Fixtures #
############


@pytest.fixture
def fake_store_client(mocker: MockerFixture) -> MockType:
    client = MagicMock()
    list_releases_result = MagicMock()
    list_releases_result.channel_map = [
        _channel_map_entry("latest/edge", revision=8),
        _channel_map_entry("latest/stable", revision=9, architecture="arm64"),
    ]
    client.get_list_releases.return_value = list_releases_result
    client.list_sdk_revisions.return_value = [
        _revision_entry(8, created_at="2026-01-19T06:17:14Z"),
        _revision_entry(
            9,
            created_at="2026-02-20T07:18:15Z",
            architecture="arm64",
        ),
        _revision_entry(10, created_at="2026-03-21T08:19:16Z"),
    ]
    return mocker.patch("sdkcraft.store.get_client", return_value=client)


#####################
# Revisions Command #
#####################


def test_revisions_lists_available_revisions(
    app_config: dict[str, Any],
    fake_store_client: MockType,
    emitter: RecordingEmitter,
) -> None:
    cmd = StoreRevisionsCommand(app_config)
    cmd.run(Namespace(sdk="my-sdk"))

    fake_store_client.return_value.get_list_releases.assert_called_once_with(
        name="my-sdk"
    )
    fake_store_client.return_value.list_sdk_revisions.assert_called_once_with("my-sdk")
    emitter.assert_message(r"CHANNEL.*REVISION.*ARCHITECTURE.*UPLOADED.*", regex=True)
    emitter.assert_message(r"latest/edge.*8.*amd64.*2026-01-19T06:17:14Z.*", regex=True)
    emitter.assert_message(
        r"latest/stable.*9.*arm64.*2026-02-20T07:18:15Z.*", regex=True
    )
    emitter.assert_message(r"-.*10.*amd64.*2026-03-21T08:19:16Z.*", regex=True)


def test_revisions_lists_revision_released_to_multiple_channels(
    app_config: dict[str, Any],
    fake_store_client: MockType,
    emitter: RecordingEmitter,
) -> None:
    fake_store_client.return_value.get_list_releases.return_value.channel_map = [
        _channel_map_entry("latest/edge", revision=8),
        _channel_map_entry("latest/beta", revision=8),
        _channel_map_entry("latest/stable", revision=8),
    ]

    cmd = StoreRevisionsCommand(app_config)
    cmd.run(Namespace(sdk="my-sdk"))

    emitter.assert_message(
        r"latest/edge,latest/beta,latest/stable.*8.*amd64.*2026-01-19T06:17:14Z.*",
        regex=True,
    )


def test_revisions_lists_revision_not_in_channel_map(
    app_config: dict[str, Any],
    fake_store_client: MockType,
    emitter: RecordingEmitter,
) -> None:
    fake_store_client.return_value.get_list_releases.return_value.channel_map = [
        _channel_map_entry("latest/edge", revision=8),
    ]
    fake_store_client.return_value.list_sdk_revisions.return_value = [
        _revision_entry(8, created_at="2026-01-19T06:17:14Z"),
        _revision_entry(11, created_at="2026-04-22T09:20:17Z"),
    ]

    cmd = StoreRevisionsCommand(app_config)
    cmd.run(Namespace(sdk="my-sdk"))

    emitter.assert_message(r"latest/edge.*8.*amd64.*2026-01-19T06:17:14Z.*", regex=True)
    emitter.assert_message(r"-.*11.*amd64.*2026-04-22T09:20:17Z.*", regex=True)


def test_revisions_displays_nothing_without_revisions(
    app_config: dict[str, Any],
    fake_store_client: MockType,
    emitter: RecordingEmitter,
) -> None:
    fake_store_client.return_value.get_list_releases.return_value.channel_map = []
    fake_store_client.return_value.list_sdk_revisions.return_value = []

    cmd = StoreRevisionsCommand(app_config)
    cmd.run(Namespace(sdk="my-sdk"))

    emitter.assert_interactions(None)
