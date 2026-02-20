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
from datetime import timedelta
from typing import Any

import craft_store

from sdkcraft._version import __version__
from sdkcraft.models.store import SdkListReleasesModel
from sdkcraft.store import constants

_HOSTNAME: str = platform.node() or "UNKNOWN"


def get_store_url() -> str:
    """Return the SDK Store URL."""
    return os.getenv("SDK_STORE_URL", constants.SDK_STORE_URL)


def get_store_upload_url() -> str:
    """Return the SDK Store Upload URL."""
    return os.getenv("SDK_STORE_UPLOAD_URL", constants.SDK_STORE_UPLOAD_URL)


def build_user_agent() -> str:
    """Build user agent string for SDKcraft."""
    return f"sdkcraft/{__version__}"


def get_client(*, ephemeral: bool = False) -> craft_store.BaseClient:
    """Store Client factory."""
    store_url = get_store_url()
    store_upload_url = get_store_upload_url()
    user_agent = build_user_agent()

    endpoints = craft_store.endpoints.Endpoints(
        namespace="sdk",
        whoami="/v1/tokens/whoami",
        tokens="/v1/tokens",
        tokens_exchange="/v1/tokens/exchange",
        valid_package_types=["sdk"],
        list_releases_model=SdkListReleasesModel,
    )

    # Use StoreClient for Candid authentication with Charmhub
    client: craft_store.BaseClient = craft_store.StoreClient(
        base_url=store_url,
        storage_base_url=store_upload_url,
        application_name="sdkcraft",
        user_agent=user_agent,
        endpoints=endpoints,
        environment_auth=constants.ENVIRONMENT_STORE_CREDENTIALS,
        ephemeral=ephemeral,
        file_fallback=True,  # Enable file-based keyring for containers
    )

    return client


class StoreClientCLI:
    """A StoreClient wrapper with CLI-specific interaction methods.

    This class wraps a StoreClient and delegates all StoreClient methods to it,
    while providing additional CLI-specific functionality like enhanced login.
    """

    def __init__(self, *, ephemeral: bool = False) -> None:
        self.store_client = get_client(ephemeral=ephemeral)
        self._base_url = get_store_url()

    def __getattr__(self, name: str) -> Any:  # noqa: ANN401
        """Delegate all undefined attributes/methods to the wrapped store_client."""
        return getattr(self.store_client, name)

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

        # StoreClient uses Candid authentication with browser-based flow
        return self.store_client.login(  # pyright: ignore[reportUnknownMemberType]
            ttl=ttl,
            permissions=acls,
            channels=channels,
            packages=_packages,
            description=description,
            **kwargs,
        )
