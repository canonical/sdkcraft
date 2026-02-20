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

"""List Releases Models for SDK Store responses."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003

from craft_store.models import MarshableModel
from craft_store.models._common_list_releases_model import PackageModel  # noqa: TC002


class SdkBaseModel(MarshableModel):
    """Base entries for SDK releases.

    :param architecture: The architecture (e.g., "arm64", "amd64").
    :param channel: The base channel (e.g., "all", "24.04").
    :param name: The base name (e.g., "all", "ubuntu").
    """

    architecture: str
    channel: str
    name: str


class SdkChannelMapModel(MarshableModel):
    """Model for the channel-map results from the SDK list_releases endpoint.

    :param base: The base specification for this release.
    :param channel: The channel this release is on (e.g., "latest/edge").
    :param expiration_date: When this release expires (if applicable).
    :param revision: The revision number.
    :param when: When this release was made.
    """

    base: SdkBaseModel
    channel: str
    expiration_date: datetime | None = None
    revision: int
    when: datetime


class SdkRevisionModel(MarshableModel):
    """Model for a revision entry from SDK list_releases.

    :param bases: List of bases this revision supports.
    :param created_at: When the revision was created.
    :param created_by: User ID of the creator.
    :param revision: The revision number.
    :param sha3_384: SHA3-384 hash of the SDK package.
    :param size: Size of the SDK package in bytes.
    :param status: Status of the revision (e.g., "released").
    :param version: Version string of the SDK.
    """

    bases: list[SdkBaseModel]
    created_at: datetime
    created_by: str
    revision: int
    sha3_384: str
    size: int
    status: str
    version: str


class SdkListReleasesModel(MarshableModel):
    """Model for the SDK list_releases endpoint.

    :param channel_map: List of channel mappings showing where revisions are released.
    :param package: Package metadata including available channels.
    :param revisions: List of all revisions for this SDK.
    """

    channel_map: list[SdkChannelMapModel]
    package: PackageModel
    revisions: list[SdkRevisionModel]
