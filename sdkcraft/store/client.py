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

"""SDKcraft Store Client."""

from __future__ import annotations

import os
import platform
import subprocess
import time
from datetime import timedelta
from typing import TYPE_CHECKING, Any

import craft_store
import keyring
import pydantic
import yaml
from craft_application.errors import CraftValidationError
from craft_cli import emit
from craft_store import errors as store_errors
from craft_store import models
from craft_store.auth import FileKeyring

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    import requests  # type: ignore[import-untyped]
    from requests_toolbelt import (  # type: ignore[import-untyped]
        MultipartEncoder,
        MultipartEncoderMonitor,
    )

from sdkcraft._version import __version__
from sdkcraft.errors import SdkcraftError
from sdkcraft.models.metadata import Metadata
from sdkcraft.models.store import SdkListReleasesModel, SdkRevisionModel
from sdkcraft.store import constants

_HOSTNAME: str = platform.node() or "UNKNOWN"
_POLL_DELAY = 1.0  # seconds between status checks
_POLL_TIMEOUT = 300.0  # 5 minutes max polling time


def get_store_url() -> str:
    """Return the SDK Store URL."""
    return os.getenv("SDK_STORE_URL", constants.SDK_STORE_URL)


def get_store_upload_url() -> str:
    """Return the SDK Store Upload URL."""
    return os.getenv("SDK_STORE_UPLOAD_URL", constants.SDK_STORE_UPLOAD_URL)


def build_user_agent() -> str:
    """Build user agent string for SDKcraft."""
    return f"sdkcraft/{__version__}"


class StoreClient(craft_store.UbuntuOneStoreClient):
    """SDK Store Client with SDK-specific API methods.

    This class wraps craft_store.BaseClient and provides SDK-specific
    API interaction methods without CLI dependencies.
    """

    def __init__(self, *, ephemeral: bool = False, use_environment_auth: bool = True) -> None:
        """Initialize the StoreClient."""
        store_url = get_store_url()
        store_upload_url = get_store_upload_url()
        user_agent = build_user_agent()

        self._base_url = store_url

        endpoints = craft_store.endpoints.Endpoints(
            namespace="sdk",
            whoami="/v1/tokens/whoami",
            tokens="/v1/tokens",
            tokens_exchange="/v1/tokens/exchange",
            valid_package_types=["sdk"],
            list_releases_model=SdkListReleasesModel,
        )

        environment_auth = (
            constants.ENVIRONMENT_STORE_CREDENTIALS if use_environment_auth else None
        )

        super().__init__(
            base_url=store_url,
            storage_base_url=store_upload_url,
            auth_url="https://login.ubuntu.com",
            application_name="sdkcraft",
            user_agent=user_agent,
            endpoints=endpoints,
            environment_auth=environment_auth,
            ephemeral=ephemeral,
            file_fallback=True,  # Enable file-based keyring for containers
        )

    def get_credentials_storage_info(self) -> str:
        """Return a human-readable description of where credentials are stored."""
        if os.getenv(constants.ENVIRONMENT_STORE_CREDENTIALS):
            return f"environment variable {constants.ENVIRONMENT_STORE_CREDENTIALS!r}"

        keyring_backend = keyring.get_keyring()
        if isinstance(keyring_backend, FileKeyring):
            return f"file: {keyring_backend.credentials_file}"

        provider = keyring_backend.name
        service = self._auth.application_name
        key = self._auth.host
        return f"system keyring ({provider}), service={service!r}, key={key!r}"

    def request(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        method: str,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Perform an authenticated request, translating stale-credential errors.

        Credentials stored by older sdkcraft versions (which used a different
        login mechanism) can't be parsed by the current auth backend. Surface
        that as an actionable error instead of an opaque parsing failure.
        """
        try:
            return super().request(method, url, params, headers, **kwargs)  # pyright: ignore[reportUnknownMemberType]
        except store_errors.CredentialsNotParseable as error:
            raise SdkcraftError(
                "Stored SDK Store credentials could not be read "
                "(they may be from an older version of sdkcraft).",
                resolution="Run 'sdkcraft logout' then 'sdkcraft login' to refresh your credentials.",
            ) from error

    def ensure_registered(self, sdk_name: str) -> None:
        """Ensure the SDK is registered on the store.

        Args:
            sdk_name: Name of the SDK to register

        Raises:
            SdkcraftError: If registration check or registration fails

        """
        try:
            registered_names = self.list_registered_names()
            is_registered = any(name.name == sdk_name for name in registered_names)

            if not is_registered:
                self.register_name(sdk_name)

        except store_errors.StoreServerError as error:
            raise SdkcraftError(f"Failed to check/register SDK: {error}") from error

    def notify_and_poll_revision(self, sdk_name: str, upload_id: str) -> int:
        """Notify the store of the revision and poll until approved.

        Args:
            sdk_name: Name of the SDK
            upload_id: Upload ID from upload_file_with_progress

        Returns:
            The revision number

        Raises:
            SdkcraftError: If notification fails or polling times out or revision is rejected

        """
        try:
            # Create revision request
            revision_request = models.RevisionsRequestModel(upload_id=upload_id)
            response = self.notify_revision(
                name=sdk_name, revision_request=revision_request
            )

        except store_errors.StoreServerError as error:
            raise SdkcraftError(f"Failed to notify revision: {error}") from error

        # Construct full status URL
        status_url = self._base_url + response.status_url

        # Poll with timeout
        start_time = time.monotonic()
        while True:
            # Check timeout
            if time.monotonic() - start_time > _POLL_TIMEOUT:
                raise SdkcraftError(
                    f"Revision polling timed out after {_POLL_TIMEOUT} seconds. "
                    "The revision may still be processing."
                )

            try:
                poll_response = self.request("GET", status_url)  # pyright: ignore[reportUnknownMemberType]
                response_data = poll_response.json()

                (revision,) = response_data["revisions"]
                status = revision["status"]

                if status == "approved":
                    return int(revision["revision"])
                if status == "rejected":
                    revision_error = revision["errors"][0]
                    raise SdkcraftError(
                        f"Revision rejected: {revision_error['code']}",
                        details=revision_error["message"],
                    )

            except store_errors.StoreServerError as error:
                raise SdkcraftError(
                    f"Failed to check revision status: {error}"
                ) from error

            time.sleep(_POLL_DELAY)

    def create_tracks(self, sdk_name: str, track_names: list[str]) -> int:
        """Create one or more tracks for an SDK on the store.

        Args:
            sdk_name: Name of the SDK to create tracks for
            track_names: List of track names to create

        Returns:
            The number of tracks created

        Raises:
            SdkcraftError: If the store request fails

        """
        tracks_payload = [{"name": name} for name in track_names]
        url = f"{self._base_url}/v1/{self._endpoints.namespace}/{sdk_name}/tracks"

        try:
            response = self.request("POST", url, json=tracks_payload)  # pyright: ignore[reportUnknownMemberType]
        except store_errors.StoreServerError as error:
            raise SdkcraftError(f"Failed to create tracks: {error}") from error

        response_data = response.json()
        if "num-tracks-created" not in response_data:
            raise SdkcraftError(
                "Unexpected store response: missing 'num-tracks-created' field"
            )
        return int(response_data["num-tracks-created"])

    def list_sdk_revisions(self, sdk_name: str) -> list[SdkRevisionModel]:
        """List all SDK revisions uploaded to the store."""
        endpoint = self._endpoints.get_revisions_endpoint(sdk_name)
        response = self.request("GET", self._base_url + endpoint)  # pyright: ignore[reportUnknownMemberType]
        response_data = response.json()

        if "revisions" not in response_data:
            raise SdkcraftError("Unexpected store response: missing 'revisions' field")

        return [
            SdkRevisionModel.unmarshal(revision)
            for revision in response_data["revisions"]
        ]


def get_client(*, ephemeral: bool = False, use_environment_auth: bool = True) -> StoreClient:
    """Store Client factory.

    Returns:
        StoreClient instance with SDK-specific API methods

    """
    return StoreClient(ephemeral=ephemeral, use_environment_auth=use_environment_auth)


class StoreClientCLI:
    """CLI-specific store client wrapper.

    This class wraps StoreClient and provides CLI-specific functionality
    like SDK metadata extraction and progress reporting.
    """

    def __init__(self, *, ephemeral: bool = False, use_environment_auth: bool = True) -> None:
        """Initialize the CLI store client."""
        self.store_client = get_client(
            ephemeral=ephemeral, use_environment_auth=use_environment_auth
        )

    def login(
        self,
        *,
        ttl: int = int(timedelta(days=365).total_seconds()),
        acls: list[str] | None = None,
        packages: list[str] | None = None,
        channels: list[str] | None = None,
        **kwargs: Any,
    ) -> str:
        """Login to the store and return credentials."""
        if packages is None:
            packages = []
        _packages = [
            craft_store.endpoints.Package(package_name=p, package_type="sdk")
            for p in packages
        ]

        if acls is None:
            acls = [
                "account-register-package",
                "account-view-packages",
                "package-manage",
                "package-manage-acl",
                "package-manage-metadata",
                "package-manage-releases",
                "package-manage-revisions",
                "package-view",
                "package-view-acl",
                "package-view-metadata",
                "package-view-metrics",
                "package-view-releases",
                "package-view-revisions",
            ]

        description = f"sdkcraft@{_HOSTNAME}"

        return self.store_client.login(  # pyright: ignore[reportUnknownMemberType]
            ttl=ttl,
            permissions=acls,
            channels=channels,
            packages=_packages,
            description=description,
            **kwargs,
        )

    def upload(
        self,
        *,
        sdk_file: Path,
        release_channels: list[str] | None = None,
    ) -> int:
        """Upload an SDK file to the store and optionally release to channels.

        This is a CLI-specific orchestration method that:
        1. Extracts SDK name from the tarball
        2. Ensures SDK is registered
        3. Uploads with progress reporting
        4. Polls for revision approval
        5. Optionally releases to channels

        Args:
            sdk_file: Path to the .sdk file to upload
            release_channels: Optional list of channels to release to after upload

        Returns:
            The revision number of the uploaded SDK

        Raises:
            SdkcraftError: If upload fails at any stage

        """
        # Extract SDK name from meta/sdk.yaml inside the tarball
        sdk_name = extract_sdk_metadata(sdk_file).name
        emit.progress(f"Uploading SDK: {sdk_name}")

        def create_progress_callback(
            encoder: MultipartEncoder,
        ) -> Callable[[MultipartEncoderMonitor], None]:
            """Create a progress callback for the upload."""
            progresser = emit.progress_bar(
                "Uploading",
                total=encoder.len,  # pyright: ignore[reportUnknownMemberType]
                delta=False,
            )

            def progress_callback(monitor: MultipartEncoderMonitor) -> None:
                """Report upload progress with absolute bytes read."""
                progresser.advance(monitor.bytes_read)  # pyright: ignore[reportUnknownMemberType]

            return progress_callback

        upload_id = self.store_client.upload_file(  # pyright: ignore[reportUnknownMemberType]
            filepath=sdk_file, monitor_callback=create_progress_callback
        )
        emit.progress(f"Upload complete. Upload ID: {upload_id}")

        emit.progress("Notifying store of new revision...")
        revision_number = self.store_client.notify_and_poll_revision(
            sdk_name, upload_id
        )
        emit.progress(f"Revision {revision_number} approved")

        if release_channels:
            emit.progress(
                f"Releasing revision {revision_number} to channels: {', '.join(release_channels)}"
            )
            release_requests = [
                models.ReleaseRequestModel(channel=channel, revision=revision_number)
                for channel in release_channels
            ]
            self.store_client.release(name=sdk_name, release_request=release_requests)
            emit.progress(f"Successfully released to: {', '.join(release_channels)}")
            emit.message(
                f"Successfully uploaded and released revision {revision_number} to {', '.join(release_channels)}"
            )
        else:
            emit.message(f"Successfully uploaded revision {revision_number}")

        return revision_number


def extract_sdk_metadata(sdk_file: Path) -> Metadata:
    """Extract SDK metadata from meta/sdk.yaml inside the .sdk tarball.

    This is a CLI-specific method that uses subprocess to extract
    and parse the SDK metadata file.

    Args:
        sdk_file: Path to the .sdk tarball

    Returns:
        The metadata from meta/sdk.yaml

    Raises:
        SdkcraftError: If extraction or parsing fails

    """
    emit.progress("Extracting SDK metadata...")

    try:
        result = subprocess.run(
            [
                "tar",
                "--extract",
                "--to-stdout",
                "--force-local",
                f"--file={sdk_file}",
                "meta/sdk.yaml",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        # Parse the YAML content using Metadata model
        yaml_data = yaml.safe_load(result.stdout)
        sdk_metadata = Metadata.model_validate(yaml_data)
    except subprocess.CalledProcessError as error:
        raise SdkcraftError(
            f"Failed to extract metadata from SDK file: {error.stderr}"
        ) from error
    except pydantic.ValidationError as error:
        raise CraftValidationError.from_pydantic(
            error, file_name="meta/sdk.yaml"
        ) from error
    except (yaml.YAMLError, ValueError) as error:
        raise SdkcraftError(f"Failed to parse SDK metadata: {error}") from error
    except Exception as error:
        raise SdkcraftError(f"Failed to read SDK metadata: {error}") from error
    else:
        emit.progress(f"Detected SDK name: {sdk_metadata.name}")
        return sdk_metadata
