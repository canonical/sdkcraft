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

"""Tests for upload command."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path  # noqa: TC003 (used at runtime in fixture)
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from craft_application import AppMetadata
from sdkcraft.commands.upload import UploadCommand
from sdkcraft.errors import SdkcraftError
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
def fake_sdk_file(tmp_path: Path) -> Path:
    """Create a fake SDK file."""
    sdk_file = tmp_path / "test-toolkit_amd64_ubuntu@24.04.sdk"
    sdk_file.write_text("name: test-toolkit\nbase: ubuntu@24.04\n")
    return sdk_file


@pytest.fixture
def fake_store_client(mocker: MockerFixture) -> MockType:
    """Mock StoreClientCLI."""
    client = MagicMock()
    client.upload.return_value = 42  # Return revision number
    return mocker.patch(
        "sdkcraft.store.StoreClientCLI",
        return_value=client,
    )


##################
# Upload Command #
##################


def test_upload_file_not_found(
    app_config: dict, fake_store_client: MockType, tmp_path: Path
):
    cmd = UploadCommand(app_config)
    non_existent = tmp_path / "doesnotexist.sdk"

    with pytest.raises(SdkcraftError, match="SDK file not found"):
        cmd.run(Namespace(sdk_file=non_existent, release=None))

    fake_store_client.return_value.upload.assert_not_called()


def test_upload_invalid_extension(
    app_config: dict, fake_store_client: MockType, tmp_path: Path
):
    cmd = UploadCommand(app_config)
    wrong_file = tmp_path / "test.txt"
    wrong_file.write_text("content")

    with pytest.raises(SdkcraftError, match="File must have .sdk extension"):
        cmd.run(Namespace(sdk_file=wrong_file, release=None))

    fake_store_client.return_value.upload.assert_not_called()


def test_upload_success_without_release(
    app_config: dict,
    fake_store_client: MockType,
    fake_sdk_file: Path,
):
    cmd = UploadCommand(app_config)
    cmd.run(Namespace(sdk_file=fake_sdk_file, release=None))

    fake_store_client.return_value.upload.assert_called_once_with(
        sdk_file=fake_sdk_file, release_channels=None
    )


def test_upload_success_with_release(
    app_config: dict,
    fake_store_client: MockType,
    fake_sdk_file: Path,
):
    cmd = UploadCommand(app_config)
    cmd.run(Namespace(sdk_file=fake_sdk_file, release="edge,2/beta"))

    # Verify StoreClientCLI was instantiated
    fake_store_client.assert_called_once()

    # Verify upload was called with parsed channels
    fake_store_client.return_value.upload.assert_called_once_with(
        sdk_file=fake_sdk_file, release_channels=["edge", "2/beta"]
    )


def test_upload_with_empty_release_channels(
    app_config: dict,
    fake_store_client: MockType,
    fake_sdk_file: Path,
):
    cmd = UploadCommand(app_config)
    cmd.run(Namespace(sdk_file=fake_sdk_file, release="  ,  , "))

    # Empty channels should result in empty list
    fake_store_client.return_value.upload.assert_called_once_with(
        sdk_file=fake_sdk_file, release_channels=[]
    )


def test_upload_parses_multiple_channels_with_whitespace(
    app_config: dict,
    fake_store_client: MockType,
    fake_sdk_file: Path,
):
    cmd = UploadCommand(app_config)
    cmd.run(Namespace(sdk_file=fake_sdk_file, release=" stable , edge,  4/beta"))

    # Verify channels are correctly parsed and trimmed
    fake_store_client.return_value.upload.assert_called_once_with(
        sdk_file=fake_sdk_file, release_channels=["stable", "edge", "4/beta"]
    )
