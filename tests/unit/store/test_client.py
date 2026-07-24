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

import keyring
import keyring.backends.fail
import pytest
from craft_store.auth import FileKeyring, MemoryKeyring
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
    """Mock UbuntuOneLogin.login_with and Auth so login() is hermetic."""
    root = mocker.MagicMock()
    root.serialize.return_value = "root-serialized"
    discharge = mocker.MagicMock()
    discharge.serialize.return_value = "discharge-serialized"

    login_with = mocker.patch.object(
        client.UbuntuOneLogin, "login_with", return_value=(root, discharge)
    )

    fake_auth = mocker.MagicMock()
    fake_auth.encode_credentials.return_value = "encoded-credentials"
    mocker.patch.object(client, "Auth", return_value=fake_auth)

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
