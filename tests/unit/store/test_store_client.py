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

"""Tests for StoreClient API methods."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from craft_store import models
from craft_store.errors import StoreServerError
from sdkcraft.errors import SdkcraftError
from sdkcraft.store.client import StoreClient, StoreClientCLI

if TYPE_CHECKING:
    from pathlib import Path

    from craft_cli.pytest_plugin import RecordingEmitter
    from pytest_mock import MockerFixture, MockType


############
# Fixtures #
############


@pytest.fixture
def fake_store_client(mocker: MockerFixture) -> MockType:
    """Mock StoreClient."""
    client = MagicMock()
    client.ensure_registered.return_value = None
    client.upload_file.return_value = "test-upload-id-123"
    client.notify_and_poll_revision.return_value = 42
    client.release.return_value = None

    return mocker.patch(
        "sdkcraft.store.client.get_client",
        return_value=client,
    )


@pytest.fixture
def fake_subprocess(mocker: MockerFixture) -> MockType:
    """Mock subprocess.run to return SDK metadata."""
    result = MagicMock()
    result.stdout = """name: test-toolkit
version: '1.0'
summary: Test SDK Toolkit
description: A test toolkit for testing purposes
architecture: amd64
sdkcraft_started_at: '2026-01-01T00:00:00'
"""
    return mocker.patch(
        "sdkcraft.store.client.subprocess.run",
        return_value=result,
    )


######################
# StoreClient Tests  #
######################


def test_ensure_registered_already_registered(mocker: MockerFixture):
    # Create a mock registered name matching the test SDK
    registered_name = MagicMock()
    registered_name.name = "test-toolkit"

    # Patch the methods directly on the StoreClient instance
    mock_list = mocker.patch.object(
        StoreClient,
        "list_registered_names",
        return_value=[registered_name],
    )
    mock_register = mocker.patch.object(StoreClient, "register_name", return_value=None)

    client = StoreClient()
    client.ensure_registered("test-toolkit")

    # Verify list was called but register was not
    mock_list.assert_called_once()
    mock_register.assert_not_called()


def test_ensure_registered_new_sdk(mocker: MockerFixture):
    # Mock list_registered_names to return empty (SDK not registered)
    mock_list = mocker.patch.object(
        StoreClient, "list_registered_names", return_value=[]
    )
    mock_register = mocker.patch.object(StoreClient, "register_name", return_value=None)

    client = StoreClient()
    client.ensure_registered("new-sdk")

    # Verify SDK was registered
    mock_list.assert_called_once()
    mock_register.assert_called_once_with("new-sdk")


def test_notify_and_poll_revision_success(mocker: MockerFixture):
    # Mock notify_revision response
    notify_response = MagicMock()
    notify_response.status_url = (
        "/v1/sdk/test-sdk/revisions/review?upload-id=test-upload-id-123"
    )

    # Mock request response for polling
    request_response = MagicMock()
    request_response.json.return_value = {
        "revisions": [
            {"revision": 42, "status": "approved", "upload-id": "test-upload-id-123"}
        ]
    }

    mock_notify = mocker.patch.object(
        StoreClient,
        "notify_revision",
        return_value=notify_response,
    )
    mock_request = mocker.patch.object(
        StoreClient, "request", return_value=request_response
    )

    client = StoreClient()
    revision = client.notify_and_poll_revision("test-sdk", "test-upload-id-123")

    assert revision == 42
    mock_notify.assert_called_once()
    mock_request.assert_called_with(
        "GET",
        "https://api.charmhub.io/v1/sdk/test-sdk/revisions/review?upload-id=test-upload-id-123",
    )


def test_notify_and_poll_revision_rejected(mocker: MockerFixture):
    notify_response = MagicMock()
    notify_response.status_url = (
        "/v1/sdk/test-sdk/revisions/review?upload-id=test-upload-id-123"
    )

    request_response = MagicMock()
    request_response.json.return_value = {
        "revisions": [
            {
                "revision": 42,
                "status": "rejected",
                "errors": [{"code": "invalid-format", "message": "Invalid SDK format"}],
                "upload-id": "test-upload-id-123",
            }
        ]
    }

    mocker.patch.object(
        StoreClient,
        "notify_revision",
        return_value=notify_response,
    )
    mocker.patch.object(StoreClient, "request", return_value=request_response)

    client = StoreClient()

    with pytest.raises(SdkcraftError, match="Revision rejected: invalid-format"):
        client.notify_and_poll_revision("test-sdk", "test-upload-id-123")


def test_notify_and_poll_revision_timeout(mocker: MockerFixture):
    # Mock notify_revision response
    notify_response = MagicMock()
    notify_response.status_url = (
        "/v1/sdk/test-sdk/revisions/review?upload-id=test-upload-id-123"
    )

    # Mock request response with pending status
    request_response = MagicMock()
    request_response.json.return_value = {
        "revisions": [
            {"revision": 42, "status": "pending", "upload-id": "test-upload-id-123"}
        ]
    }

    mocker.patch.object(
        StoreClient,
        "notify_revision",
        return_value=notify_response,
    )
    mocker.patch.object(StoreClient, "request", return_value=request_response)

    # Mock time to immediately trigger timeout
    fake_time = mocker.patch("sdkcraft.store.client.time")
    fake_time.monotonic.side_effect = [0, 301]  # Start at 0, then exceed timeout

    client = StoreClient()

    with pytest.raises(SdkcraftError, match="Revision polling timed out"):
        client.notify_and_poll_revision("test-sdk", "test-upload-id-123")


#########################
# StoreClientCLI Tests  #
#########################


def test_cli_upload_success_without_release(
    fake_store_client: MockType,
    fake_subprocess: MockType,
    emitter: RecordingEmitter,
    fake_sdk_file: Path,
):
    client = StoreClientCLI()
    revision = client.upload(sdk_file=fake_sdk_file, release_channels=None)

    assert revision == 42

    fake_subprocess.assert_called_once_with(
        [
            "tar",
            "--extract",
            "--to-stdout",
            "--force-local",
            f"--file={fake_sdk_file}",
            "meta/sdk.yaml",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    fake_store_client.return_value.upload_file.assert_called_once()
    fake_store_client.return_value.notify_and_poll_revision.assert_called_once_with(
        "test-toolkit", "test-upload-id-123"
    )
    fake_store_client.return_value.release.assert_not_called()

    emitter.assert_message("Successfully uploaded revision 42")


def test_cli_upload_success_with_release(
    fake_store_client: MockType,
    fake_subprocess: MockType,
    emitter: RecordingEmitter,
    fake_sdk_file: Path,
):
    client = StoreClientCLI()
    revision = client.upload(sdk_file=fake_sdk_file, release_channels=["edge", "beta"])

    assert revision == 42

    fake_subprocess.assert_called_once_with(
        [
            "tar",
            "--extract",
            "--to-stdout",
            "--force-local",
            f"--file={fake_sdk_file}",
            "meta/sdk.yaml",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    fake_store_client.return_value.upload_file.assert_called_once()
    fake_store_client.return_value.notify_and_poll_revision.assert_called_once_with(
        "test-toolkit", "test-upload-id-123"
    )
    fake_store_client.return_value.release.assert_called_once_with(
        name="test-toolkit",
        release_request=[
            models.ReleaseRequestModel(channel="edge", revision=42),
            models.ReleaseRequestModel(channel="beta", revision=42),
        ],
    )

    emitter.assert_message(
        "Successfully uploaded and released revision 42 to edge, beta"
    )


############################
# StoreClient.create_tracks #
############################


def test_create_tracks_success(mocker: MockerFixture):
    response = MagicMock()
    response.json.return_value = {"num-tracks-created": 2}

    mock_request = mocker.patch.object(StoreClient, "request", return_value=response)

    client = StoreClient()
    num_created = client.create_tracks("my-sdk", ["1.26", "1.25"])

    assert num_created == 2
    mock_request.assert_called_once_with(
        "POST",
        "https://api.charmhub.io/v1/sdk/my-sdk/tracks",
        json=[{"name": "1.26"}, {"name": "1.25"}],
    )


def test_create_tracks_server_error(mocker: MockerFixture):
    mocker.patch.object(
        StoreClient,
        "request",
        side_effect=StoreServerError(
            MagicMock(status_code=500, headers={}, content=b"")
        ),
    )

    client = StoreClient()

    with pytest.raises(SdkcraftError, match="Failed to create tracks"):
        client.create_tracks("my-sdk", ["1.26"])
