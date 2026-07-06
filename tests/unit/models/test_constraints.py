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

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError
from sdkcraft.models.constraints import (
    PROJECT_NAME_REGEX,
    ChannelName,
    CleanAbsPath,
    DeviceID,
    Endpoint,
    FileMode,
    PlugName,
    ProjectName,
    UserGroupID,
)

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


plug_name_adapter: TypeAdapter[PlugName] = TypeAdapter(PlugName)


def test_plug_name_invalid():
    with pytest.raises(ValidationError):
        plug_name_adapter.validate_python("Abc")

    with pytest.raises(ValidationError):
        plug_name_adapter.validate_python("1bc")

    with pytest.raises(ValidationError):
        plug_name_adapter.validate_python("-abc")

    with pytest.raises(ValidationError):
        plug_name_adapter.validate_python("abc-")

    with pytest.raises(ValidationError):
        plug_name_adapter.validate_python("a--b--c")


device_id_adapter: TypeAdapter[DeviceID] = TypeAdapter(DeviceID)


@pytest.mark.parametrize(
    "value", ["6001", "0x6001", "403", "0000", "00ffff", "FFEE", "d", "0xA"]
)
def test_device_id_valid(value: str):
    assert device_id_adapter.validate_python(value) == value


@pytest.mark.parametrize("value", ["", "60011", "ABCG", "z001", "60_1", " abcd "])
def test_device_id_invalid(value: str):
    with pytest.raises(ValidationError):
        device_id_adapter.validate_python(value)


clean_abs_path_adapter: TypeAdapter[CleanAbsPath] = TypeAdapter(CleanAbsPath)


@pytest.mark.parametrize(
    "value",
    ["/mnt", "/run/user/1000/sdk", "/home/workshop/.cache/dir"],
)
def test_clean_abs_path_valid(*, value: str):
    clean_abs_path_adapter.validate_python(value)


@pytest.mark.parametrize(
    "value",
    ["relative/path", "/tmp/../etc/gshadow", "/../path", "/mnt/.", "/home//workshop"],
)
def test_clean_abs_path_invalid(value: str):
    with pytest.raises(ValidationError):
        clean_abs_path_adapter.validate_python(value)


file_mode_adapter: TypeAdapter[FileMode] = TypeAdapter(FileMode)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, 0),
        (0o644, 0o644),
        ("0644", 0o644),
        ("0o644", 0o644),
        (0o700, 0o700),
        ("0700", 0o700),
        ("0o700", 0o700),
        (0o777, 0o777),
        ("0777", 0o777),
        ("0o777", 0o777),
    ],
)
def test_file_mode_valid(*, value: int | str, expected: int):
    assert file_mode_adapter.validate_python(value) == expected


@pytest.mark.parametrize(
    "value",
    ["invalid-value", -1, "099", "0o99", "0_o644", 0o1000, "1000", "01000", "0o1000"],
)
def test_file_mode_invalid(value: int | str):
    with pytest.raises(ValidationError):
        file_mode_adapter.validate_python(value)


user_group_id_adapter: TypeAdapter[UserGroupID] = TypeAdapter(UserGroupID)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, 0),
        ("0", 0),
        (1000, 1000),
        ("1000", 1000),
        (0xFFFFFFFE, 0xFFFFFFFE),
    ],
)
def test_user_group_id_valid(*, value: int | str, expected: int):
    assert user_group_id_adapter.validate_python(value) == expected


@pytest.mark.parametrize("value", ["invalid-value", -1, (1 << 32) - 1, (1 << 32)])
def test_user_group_id_invalid(value: int | str):
    with pytest.raises(ValidationError):
        user_group_id_adapter.validate_python(value)


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
def test_endpoint_valid(value: str):
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
def test_endpoint_invalid(value: str):
    with pytest.raises(ValidationError):
        endpoint_adapter.validate_python(value)


@pytest.mark.parametrize(
    "value",
    [
        "stable",
        "candidate",
        "beta",
        "edge",
        "latest/stable",
        "latest/edge",
        "1.0/candidate",
        "stable/my-branch",
        "latest/beta/my-branch",
    ],
)
def test_channel_name_valid(value: str):
    assert TypeAdapter(ChannelName).validate_python(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "invalid",
        "latest/invalid",
        "latest/invalid/branch",
    ],
)
def test_channel_name_invalid(value: str):
    with pytest.raises(ValidationError):
        TypeAdapter(ChannelName).validate_python(value)
