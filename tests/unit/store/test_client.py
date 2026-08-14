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

"""Tests for store client."""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING
from unittest.mock import ANY

import craft_store
import keyring
import keyring.backends.fail
import pytest
from craft_store.auth import FileKeyring, MemoryKeyring
from craft_store.errors import (
    CredentialsAlreadyAvailable,
    CredentialsNotParseable,
    CredentialsUnavailable,
)
from sdkcraft.errors import SdkcraftError
from sdkcraft.store import client

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture, MockType

############
# Fixtures #
############


@pytest.fixture
def fake_client(mocker: MockerFixture) -> MockType:
    """Forces get_client to return a fake craft_store.UbuntuOneStoreClient"""
    store_client = mocker.patch("craft_store.UbuntuOneStoreClient", autospec=True)
    mocker.patch("sdkcraft.store.client.get_client", return_value=store_client)
    return store_client


#####################
# Store URLs Tests #
#####################


def test_get_store_url_default():
    assert client.get_store_url() == "https://api.charmhub.io"


def test_get_store_url_from_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SDK_STORE_URL", "https://custom.api")
    assert client.get_store_url() == "https://custom.api"


def test_get_store_upload_url_default():
    assert client.get_store_upload_url() == "https://storage.snapcraftcontent.com"


def test_get_store_upload_url_from_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SDK_STORE_UPLOAD_URL", "https://custom.storage")
    assert client.get_store_upload_url() == "https://custom.storage"


####################
# User Agent Tests #
####################


def test_build_user_agent_format():
    user_agent = client.build_user_agent()
    assert user_agent.startswith("sdkcraft/")


###############
# Login Tests #
###############


@pytest.fixture
def fake_u1_login(mocker: MockerFixture) -> MockType:
    """Mock the login flow (SSO, exchange, and keyring) so login() is hermetic."""
    login_with = mocker.patch.object(client.UbuntuOneLogin, "login_with")

    fake_auth = mocker.MagicMock()
    fake_auth.encode_credentials.return_value = "encoded-credentials"
    mocker.patch.object(client, "Auth", return_value=fake_auth)

    # login() builds a StoreClient and exchanges the macaroons for a token.
    mocker.patch.object(client, "get_client")
    mocker.patch.object(client.craft_store, "UbuntuOneAuth")

    return login_with


def _default_acls() -> list[str]:
    return [
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


def test_login_default(fake_u1_login: MockType):
    client.StoreClientCLI().login(email="user@example.com", password="hunter2")  # noqa: S106

    fake_u1_login.assert_called_once_with(
        email="user@example.com",
        password="hunter2",  # noqa: S106
        otp=None,
        base_url="https://api.charmhub.io",
        login_url="https://login.ubuntu.com",
        application_name="sdkcraft",
        store_auth=ANY,
        permissions=_default_acls(),
        packages=None,
        channels=None,
        ttl=31536000,
    )


def test_login_with_params(fake_u1_login: MockType):
    client.StoreClientCLI().login(
        email="user@example.com",
        password="hunter2",  # noqa: S106
        otp="123456",
        ttl=20,
        acls=["package-view", "package-manage"],
        packages=["fake-sdk", "fake-other-sdk"],
        channels=["stable/fake", "edge/fake"],
    )

    fake_u1_login.assert_called_once_with(
        email="user@example.com",
        password="hunter2",  # noqa: S106
        otp="123456",
        base_url="https://api.charmhub.io",
        login_url="https://login.ubuntu.com",
        application_name="sdkcraft",
        store_auth=ANY,
        permissions=["package-view", "package-manage"],
        packages=[
            {"type": "sdk", "name": "fake-sdk"},
            {"type": "sdk", "name": "fake-other-sdk"},
        ],
        channels=["stable/fake", "edge/fake"],
        ttl=20,
    )


def test_login_with_none_packages(fake_u1_login: MockType):
    client.StoreClientCLI().login(
        email="user@example.com",
        password="hunter2",  # noqa: S106
        packages=None,
    )

    assert fake_u1_login.call_args.kwargs["packages"] is None


def test_login_returns_credentials(fake_u1_login: MockType):
    result = client.StoreClientCLI().login(
        email="user@example.com",
        password="hunter2",  # noqa: S106
    )

    assert result == "encoded-credentials"


######################################
# Credentials Storage Info Tests     #
######################################


def test_credentials_storage_info_env_var(
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
):
    """Reports the env var name when credentials come from the environment."""
    monkeypatch.setenv(
        "SDKCRAFT_STORE_CREDENTIALS", base64.b64encode(b"test-creds").decode()
    )
    mocker.patch("keyring.set_keyring")
    mocker.patch("keyring.get_keyring", return_value=MemoryKeyring())
    store_client = client.StoreClient()

    assert store_client.get_credentials_storage_info() == (
        "environment variable 'SDKCRAFT_STORE_CREDENTIALS'"
    )


def test_credentials_storage_info_file_keyring(
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    """Reports the file path when the FileKeyring backend is in use."""
    monkeypatch.delenv("SDKCRAFT_STORE_CREDENTIALS", raising=False)
    mocker.patch(
        "craft_store.auth.BaseDirectory.save_data_path", return_value=str(tmp_path)
    )
    mocker.patch("keyring.set_keyring")
    file_keyring = FileKeyring("sdkcraft")
    mocker.patch(
        "keyring.get_keyring",
        side_effect=[keyring.backends.fail.Keyring(), file_keyring, file_keyring],
    )
    store_client = client.StoreClient()

    assert store_client.get_credentials_storage_info() == (
        f"file: {tmp_path / 'credentials.json'}"
    )


def test_credentials_storage_info_system_keyring(
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
):
    """Reports provider name, service and key for system keyring backends."""
    monkeypatch.delenv("SDKCRAFT_STORE_CREDENTIALS", raising=False)
    mock_keyring = mocker.MagicMock()
    mock_keyring.name = "SecretService Keyring"
    mocker.patch("keyring.get_keyring", return_value=mock_keyring)
    store_client = client.StoreClient()

    assert store_client.get_credentials_storage_info() == (
        "system keyring (SecretService Keyring), "
        "service='sdkcraft', key='api.charmhub.io'"
    )


######################################
# USSO Exchange Auth Tests           #
######################################


def test_get_authorization_header_uses_stored_token(mocker: MockerFixture):
    """The auth header is built from the stored, already-exchanged token."""
    store_client = client.StoreClient(ephemeral=True, use_environment_auth=False)

    mocker.patch.object(
        store_client._auth, "get_credentials", return_value="store-token"
    )

    assert store_client._get_authorization_header() == "Macaroon store-token"


def test_exchange_via_ubuntu_one_auth_on_login(mocker: MockerFixture):
    """Login exchanges the freshly issued macaroons for a store token."""
    mocker.patch.object(client.UbuntuOneLogin, "login_with")
    mocker.patch.object(client, "get_client")

    fake_auth = mocker.MagicMock()
    fake_auth.get_credentials.return_value = "store-token"
    fake_auth.encode_credentials.return_value = "encoded-credentials"
    mocker.patch.object(client, "Auth", return_value=fake_auth)

    u1_auth = mocker.patch.object(client.craft_store, "UbuntuOneAuth")

    result = client.StoreClientCLI().login(
        email="user@example.com",
        password="hunter2",  # noqa: S106
    )

    u1_auth.assert_called_once_with(
        auth=fake_auth,
        api_base_url="https://api.charmhub.io",
        client_description="sdkcraft",
    )
    u1_auth.return_value.get_token_from_keyring.assert_called_once()
    fake_auth.encode_credentials.assert_called_once_with("store-token")
    assert result == "encoded-credentials"


######################################
# Stale Credentials Tests            #
######################################


def test_request_translates_stale_credentials_error(mocker: MockerFixture):
    """Credentials left over from an older sdkcraft version raise a clear error."""
    mocker.patch.object(
        craft_store.UbuntuOneStoreClient,
        "request",
        side_effect=CredentialsNotParseable("Expected valid Ubuntu One credentials"),
    )
    store_client = client.StoreClient()

    with pytest.raises(SdkcraftError, match="Stored SDK Store credentials"):
        store_client.request("GET", "https://api.charmhub.io/v1/tokens/whoami")


def test_request_translates_missing_credentials_error(mocker: MockerFixture):
    """Running a store command without logging in points the user at login."""
    mocker.patch.object(
        craft_store.UbuntuOneStoreClient,
        "request",
        side_effect=CredentialsUnavailable("sdkcraft", "api.charmhub.io"),
    )
    store_client = client.StoreClient()

    with pytest.raises(SdkcraftError, match="not logged in") as exc_info:
        store_client.request("GET", "https://api.charmhub.io/v1/tokens/whoami")

    assert exc_info.value.resolution == "Run 'sdkcraft login' to authenticate."


######################################
# Environment Auth Opt-Out Tests     #
######################################


def test_use_environment_auth_false_ignores_env_var(monkeypatch: pytest.MonkeyPatch):
    """A stale SDKCRAFT_STORE_CREDENTIALS must not block login/logout via ensure_no_credentials.

    Regression test: login (including --export, which uses ephemeral=True) always passed
    environment_auth to craft_store, so a leftover env var was loaded as "existing"
    credentials before login even ran, tripping CredentialsAlreadyAvailable with no way
    to recover (logout only clears the persistent keyring, not the env var).
    """
    monkeypatch.setenv(
        "SDKCRAFT_STORE_CREDENTIALS",
        base64.b64encode(b'{"t": "macaroon", "v": "stale"}').decode(),
    )

    store_client = client.StoreClient(ephemeral=True, use_environment_auth=False)

    # Should not raise CredentialsAlreadyAvailable: the env var must be ignored entirely.
    store_client._auth.ensure_no_credentials()


def test_use_environment_auth_true_still_honors_env_var(
    monkeypatch: pytest.MonkeyPatch,
):
    """Normal (non-login) command usage must still pick up SDKCRAFT_STORE_CREDENTIALS."""
    monkeypatch.setenv(
        "SDKCRAFT_STORE_CREDENTIALS",
        base64.b64encode(b'{"t": "macaroon", "v": "stale"}').decode(),
    )

    store_client = client.StoreClient(ephemeral=True, use_environment_auth=True)

    with pytest.raises(CredentialsAlreadyAvailable):
        store_client._auth.ensure_no_credentials()
