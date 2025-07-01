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
from sdkcraft.models.constraints import PROJECT_NAME_REGEX, Endpoint, ProjectName

project_name_adapter: TypeAdapter[ProjectName] = TypeAdapter(ProjectName)


def test_project_name_inherits_constraints():
    with pytest.raises(ValidationError):
        project_name_adapter.validate_python("ABC")

    with pytest.raises(ValidationError):
        project_name_adapter.validate_python("123")

    with pytest.raises(ValidationError):
        project_name_adapter.validate_python("-abc")

    with pytest.raises(ValidationError):
        project_name_adapter.validate_python("a--b--c")

    name = project_name_adapter.validate_python("123-abc")
    assert name == "123-abc"


def test_project_name_forbids_reserved():
    with pytest.raises(
        ValidationError,
        match=r"invalid name: Names cannot be 'system', 'sketch' or start with 'project-'\.",
    ):
        project_name_adapter.validate_python("system")

    with pytest.raises(
        ValidationError,
        match=r"invalid name: Names cannot be 'system', 'sketch' or start with 'project-'\.",
    ):
        project_name_adapter.validate_python("sketch")

    with pytest.raises(
        ValidationError,
        match=r"invalid name: Names cannot be 'system', 'sketch' or start with 'project-'\.",
    ):
        project_name_adapter.validate_python("project-foo")

    name = project_name_adapter.validate_python("system-seller")
    assert name == "system-seller"
    name = project_name_adapter.validate_python("my-project-1")
    assert name == "my-project-1"
    name = project_name_adapter.validate_python("roughsketch")
    assert name == "roughsketch"


def test_project_name_json_schema_includes_pattern():
    schema = project_name_adapter.json_schema()
    assert schema["pattern"] == PROJECT_NAME_REGEX


endpoint_adapter: TypeAdapter[Endpoint] = TypeAdapter(Endpoint)


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
def test_endpoint_valid(value: list[str]):
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
def test_endpoint_invalid(value: list[str]):
    with pytest.raises(ValidationError):
        endpoint_adapter.validate_python(value)
