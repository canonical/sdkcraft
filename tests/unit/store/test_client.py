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

from typing import TYPE_CHECKING
from unittest.mock import call

import pytest
from craft_store import endpoints
from sdkcraft.store import client

if TYPE_CHECKING:
    from pytest_mock import MockerFixture, MockType

############
# Fixtures #
############


@pytest.fixture
def fake_client(mocker: MockerFixture) -> MockType:
    """Forces get_client to return a fake craft_store.StoreClient"""
    store_client = mocker.patch("craft_store.StoreClient", autospec=True)
    mocker.patch("sdkcraft.store.client.get_client", return_value=store_client)
    return store_client


@pytest.fixture
def fake_hostname(mocker: MockerFixture) -> MockType:
    """Mock _HOSTNAME constant to return a fixed hostname."""
    return mocker.patch.object(client, "_HOSTNAME", "fake-host")


#####################
# Store URLs Tests #
#####################


def test_get_store_url_default():
    assert client.get_store_url() == "https://api.staging.charmhub.io"


def test_get_store_url_from_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SDK_STORE_URL", "https://custom.api")
    assert client.get_store_url() == "https://custom.api"


def test_get_store_upload_url_default():
    assert (
        client.get_store_upload_url() == "https://storage.staging.snapcraftcontent.com"
    )


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


@pytest.mark.usefixtures("fake_hostname")
def test_login_default(fake_client: MockType):
    client.StoreClientCLI().login()

    assert fake_client.login.mock_calls == [
        call(
            ttl=31536000,
            permissions=[
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
            ],
            channels=None,
            packages=[],
            description="sdkcraft@fake-host",
        )
    ]


@pytest.mark.usefixtures("fake_hostname")
def test_login_with_params(fake_client: MockType):
    client.StoreClientCLI().login(
        ttl=20,
        acls=["package-view", "package-manage"],
        packages=["fake-sdk", "fake-other-sdk"],
        channels=["stable/fake", "edge/fake"],
    )

    assert fake_client.login.mock_calls == [
        call(
            ttl=20,
            permissions=[
                "package-view",
                "package-manage",
            ],
            channels=["stable/fake", "edge/fake"],
            packages=[
                endpoints.Package(package_name="fake-sdk", package_type="sdk"),
                endpoints.Package(package_name="fake-other-sdk", package_type="sdk"),
            ],
            description="sdkcraft@fake-host",
        )
    ]


@pytest.mark.usefixtures("fake_hostname")
def test_login_with_custom_ttl(fake_client: MockType):
    client.StoreClientCLI().login(ttl=7200)

    assert fake_client.login.mock_calls == [
        call(
            ttl=7200,
            permissions=[
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
            ],
            channels=None,
            packages=[],
            description="sdkcraft@fake-host",
        )
    ]


@pytest.mark.usefixtures("fake_hostname")
def test_login_with_custom_acls(fake_client: MockType):
    custom_acls = ["package-view", "package-manage"]
    client.StoreClientCLI().login(acls=custom_acls)

    assert fake_client.login.mock_calls == [
        call(
            ttl=31536000,
            permissions=custom_acls,
            channels=None,
            packages=[],
            description="sdkcraft@fake-host",
        )
    ]


@pytest.mark.usefixtures("fake_hostname")
def test_login_with_channels(fake_client: MockType):
    channels = ["stable", "edge"]
    client.StoreClientCLI().login(channels=channels)

    assert fake_client.login.mock_calls == [
        call(
            ttl=31536000,
            permissions=[
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
            ],
            channels=channels,
            packages=[],
            description="sdkcraft@fake-host",
        )
    ]


@pytest.mark.usefixtures("fake_hostname")
def test_login_with_packages(fake_client: MockType):
    client.StoreClientCLI().login(packages=["my-sdk", "other-sdk"])

    assert fake_client.login.mock_calls == [
        call(
            ttl=31536000,
            permissions=[
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
            ],
            channels=None,
            packages=[
                endpoints.Package(package_name="my-sdk", package_type="sdk"),
                endpoints.Package(package_name="other-sdk", package_type="sdk"),
            ],
            description="sdkcraft@fake-host",
        )
    ]


@pytest.mark.usefixtures("fake_hostname")
def test_login_with_empty_packages(fake_client: MockType):
    client.StoreClientCLI().login(packages=[])

    assert fake_client.login.mock_calls == [
        call(
            ttl=31536000,
            permissions=[
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
            ],
            channels=None,
            packages=[],
            description="sdkcraft@fake-host",
        )
    ]


@pytest.mark.usefixtures("fake_hostname")
def test_login_with_none_packages(fake_client: MockType):
    client.StoreClientCLI().login(packages=None)

    assert fake_client.login.mock_calls == [
        call(
            ttl=31536000,
            permissions=[
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
            ],
            channels=None,
            packages=[],
            description="sdkcraft@fake-host",
        )
    ]


@pytest.mark.usefixtures("fake_hostname")
def test_login_returns_credentials(fake_client: MockType):
    fake_client.login.return_value = "test-credentials"

    result = client.StoreClientCLI().login()

    assert result == "test-credentials"
