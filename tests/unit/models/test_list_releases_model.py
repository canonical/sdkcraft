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

"""Tests for SDK list releases model."""

from __future__ import annotations

from datetime import UTC, datetime

from sdkcraft.models.store import (
    SdkBaseModel,
    SdkChannelMapModel,
    SdkListReleasesModel,
    SdkRevisionModel,
)


def test_sdk_base_model():
    """Test SdkBaseModel unmarshaling."""
    data = {
        "architecture": "arm64",
        "channel": "all",
        "name": "all",
    }

    base = SdkBaseModel.unmarshal(data)

    assert base.architecture == "arm64"
    assert base.channel == "all"
    assert base.name == "all"


def test_sdk_channel_map_model():
    """Test SdkChannelMapModel unmarshaling."""
    data = {
        "base": {
            "architecture": "arm64",
            "channel": "all",
            "name": "all",
        },
        "channel": "latest/edge",
        "expiration-date": None,
        "revision": 1,
        "when": "2026-01-19T06:20:26Z",
    }

    channel_map = SdkChannelMapModel.unmarshal(data)

    assert channel_map.channel == "latest/edge"
    assert channel_map.revision == 1
    assert channel_map.expiration_date is None
    assert channel_map.when == datetime(2026, 1, 19, 6, 20, 26, tzinfo=UTC)
    assert channel_map.base.architecture == "arm64"


def test_sdk_revision_model():
    """Test SdkRevisionModel unmarshaling."""
    data = {
        "bases": [
            {
                "architecture": "arm64",
                "channel": "all",
                "name": "all",
            }
        ],
        "created-at": "2026-01-19T06:17:14Z",
        "created-by": "CqyWllG7eo6hDoj2sMRtj6dFUtiU7DEK",
        "revision": 1,
        "sha3-384": "3ffbfe6ca0f4822f42ba57947b7a5e095b3df9e21e5ddd6b433ef7e0e08396c4c2bc5c75f21326d93d8efcdb26bf352c",
        "size": 59422629,
        "status": "released",
        "version": "1.24.6",
    }

    revision = SdkRevisionModel.unmarshal(data)

    assert revision.revision == 1
    assert revision.created_by == "CqyWllG7eo6hDoj2sMRtj6dFUtiU7DEK"
    assert revision.version == "1.24.6"
    assert revision.status == "released"
    assert revision.size == 59422629
    assert len(revision.bases) == 1
    assert revision.bases[0].architecture == "arm64"


def test_sdk_list_releases_model():
    """Test SdkListReleasesModel unmarshaling with full API response."""
    data = {
        "channel-map": [
            {
                "base": {
                    "architecture": "arm64",
                    "channel": "all",
                    "name": "all",
                },
                "channel": "latest/edge",
                "expiration-date": None,
                "revision": 1,
                "when": "2026-01-19T06:20:26Z",
            }
        ],
        "package": {
            "channels": [
                {
                    "branch": None,
                    "fallback": None,
                    "name": "latest/stable",
                    "risk": "stable",
                    "track": "latest",
                },
                {
                    "branch": None,
                    "fallback": "latest/stable",
                    "name": "latest/candidate",
                    "risk": "candidate",
                    "track": "latest",
                },
                {
                    "branch": None,
                    "fallback": "latest/candidate",
                    "name": "latest/beta",
                    "risk": "beta",
                    "track": "latest",
                },
                {
                    "branch": None,
                    "fallback": "latest/beta",
                    "name": "latest/edge",
                    "risk": "edge",
                    "track": "latest",
                },
            ]
        },
        "revisions": [
            {
                "bases": [
                    {
                        "architecture": "arm64",
                        "channel": "all",
                        "name": "all",
                    }
                ],
                "created-at": "2026-01-19T06:17:14Z",
                "created-by": "CqyWllG7eo6hDoj2sMRtj6dFUtiU7DEK",
                "revision": 1,
                "sha3-384": "3ffbfe6ca0f4822f42ba57947b7a5e095b3df9e21e5ddd6b433ef7e0e08396c4c2bc5c75f21326d93d8efcdb26bf352c",
                "size": 59422629,
                "status": "released",
                "version": "1.24.6",
            }
        ],
    }

    releases = SdkListReleasesModel.unmarshal(data)

    assert len(releases.channel_map) == 1
    assert len(releases.revisions) == 1
    assert len(releases.package.channels) == 4

    assert releases.channel_map[0].channel == "latest/edge"
    assert releases.channel_map[0].revision == 1

    assert releases.revisions[0].version == "1.24.6"
    assert releases.revisions[0].revision == 1
    assert releases.revisions[0].created_by == "CqyWllG7eo6hDoj2sMRtj6dFUtiU7DEK"
    assert (
        releases.revisions[0].sha3_384
        == "3ffbfe6ca0f4822f42ba57947b7a5e095b3df9e21e5ddd6b433ef7e0e08396c4c2bc5c75f21326d93d8efcdb26bf352c"
    )

    assert releases.package.channels[0].name == "latest/stable"
    assert releases.package.channels[0].fallback is None
    assert releases.package.channels[3].name == "latest/edge"
    assert releases.package.channels[3].fallback == "latest/beta"
