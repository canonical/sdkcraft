# This file is part of sdkcraft.
#
# Copyright 2024 Canonical Ltd.
#
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the GNU General Public License version 3, as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranties of MERCHANTABILITY,
#  SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Tests for type constraints."""

import pytest
from pydantic import TypeAdapter, ValidationError
from sdkcraft.models.constraints import Endpoint, ProjectName

project_name_adapter = TypeAdapter(ProjectName)


def test_project_name_inherits_constraints():
    with pytest.raises(ValidationError):
        project_name_adapter.validate_python("!@#$%")


def test_project_name_forbids_reserved():
    with pytest.raises(
        ValidationError,
        match="'system' is a reserved SDK name, please choose another name.",
    ):
        project_name_adapter.validate_python("system")


endpoint_adapter = TypeAdapter(Endpoint)


@pytest.mark.parametrize(
    "value",
    [
        "/run/service.sock",
        "@abstract.sock",
        "$HOME/.local/state/service.sock",
        "$XDG_RUNTIME_DIR/service.sock",
        "1.2.3.4:56789/tcp",
        "9.8.7.6:54321/udp",
        "1.2.3.4:56789",
        "1.2.3.4/tcp",
        "56789/udp",
        "1.2.3.4",
        "56789",
        "tcp",
        "udp",
        "localhost:56789/tcp",
        "ip6-localhost/udp",
        "ip6-loopback",
        "[::1]:56789",
        "[::]",
        "::",
    ],
)
def test_endpoint_valid(value):
    assert endpoint_adapter.validate_python(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "$FOO/bar",
        "0.1.2.3.4:56789/tcp",
        "0.1.2.3:456789/tcp",
        "example.com:54321/udp",
        "localhost:54321/path",
        "localhost:54321?query",
        "localhost:54321#fragment",
        "http:localhost",
        "http:localhost:54321",
        "http://localhost",
        "http://localhost:54321",
        "[1.2.3.4]:56789",
        "1.2.3.4:/tcp",
        ":56789/udp",
    ],
)
def test_endpoint_invalid(value):
    with pytest.raises(ValidationError):
        endpoint_adapter.validate_python(value)
