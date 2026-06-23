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
"""Tests for project models."""

from __future__ import annotations

from typing import Any

import pytest
import yaml
from craft_application import models
from pydantic import AnyUrl, TypeAdapter, ValidationError
from sdkcraft.models.project import (
    CameraPlug,
    CustomDevicePlug,
    DesktopPlug,
    GPUPlug,
    MountPlug,
    MountSlot,
    Part,
    Plugs,
    Project,
    SSHAgentPlug,
)


def test_project_create_valid(project_data: dict[str, Any]):
    project = Project.unmarshal(project_data)
    assert project.name == "default"
    assert project.title == "default title"
    assert project.version == "1.0"
    assert project.summary == "default project"
    assert project.description == "default project"
    assert project.base == "ubuntu@22.04"
    assert project.build_base is None
    assert project.platforms == {
        "ppc64el": models.Platform(build_for=["ppc64el"], build_on=["ppc64el"]),
    }
    assert project.contact == "requests@canonical.com"
    assert project.issues == "https://github.com/canonical/sdks/issues"
    assert project.source_code == AnyUrl("https://github.com/canonical/sdks")
    assert project.website == AnyUrl("https://github.com/canonical/default-sdk")
    assert project.license == "MIT"
    assert project.adopt_info is None
    assert project.plugs == {
        "mount": MountPlug(interface="mount", workshop_target="/path"),
    }
    assert project.slots == {}
    assert project.parts == {"default-part": {"plugin": "nil"}}
    assert project.package_repositories is None


custom_device_adapter: TypeAdapter[CustomDevicePlug] = TypeAdapter(CustomDevicePlug)


def test_custom_device_plug_all_filters():
    plug = {
        "interface": "custom-device",
        "subsystem": "tty",
        "productid": "6001",
        "vendorid": "0403",
    }

    result = custom_device_adapter.validate_python(plug)
    assert result.subsystem == "tty"
    assert result.productid == "6001"
    assert result.vendorid == "0403"


@pytest.mark.parametrize("subsystem", ["accel", "usb"])
def test_custom_device_plug_subsystem(subsystem: str):
    plug = {"interface": "custom-device", "subsystem": subsystem}

    result = custom_device_adapter.validate_python(plug)
    assert result.subsystem == subsystem
    assert result.vendorid == ""
    assert result.productid == ""


def test_custom_device_plug_vendorid():
    plug = {"interface": "custom-device", "vendorid": "0403"}

    result = custom_device_adapter.validate_python(plug)
    assert result.subsystem == ""
    assert result.vendorid == "0403"
    assert result.productid == ""


def test_custom_device_plug_productid():
    plug = {"interface": "custom-device", "productid": "6001"}

    with pytest.raises(ValidationError):
        custom_device_adapter.validate_python(plug)


def test_custom_device_plug_no_filter():
    plug = {"interface": "custom-device"}

    with pytest.raises(ValidationError):
        custom_device_adapter.validate_python(plug)


@pytest.mark.parametrize("path", ["$SDK", "$SDK/subdir"])
def test_mount_plug_sdk_variable(path: str):
    plug = {"interface": "mount", "workshop-target": path}

    result = MountPlug.unmarshal(plug)
    assert result.workshop_target == path


@pytest.mark.parametrize("path", ["$SDK", "$SDK/subdir"])
def test_mount_slot_sdk_variable(path: str):
    slot = {"interface": "mount", "workshop-source": path}

    result = MountSlot.unmarshal(slot)
    assert result.workshop_source == path


def test_mount_slot_invalid_variable():
    slot = {"interface": "mount", "workshop-source": "$HOME/subdir"}

    with pytest.raises(ValidationError):
        MountSlot.unmarshal(slot)


@pytest.mark.parametrize(
    "path",
    [
        "/home/workshop",
        "/home/workshop/.cache/dir",
        "/project",
        "/project/.cache",
        "/run/user/1000",
        "/run/user/1000/sdk",
    ],
)
def test_mount_plug_defaults_workshop(path: str):
    plug = {"interface": "mount", "workshop-target": path}

    result = MountPlug.unmarshal(plug)
    assert result.uid == 1000
    assert result.gid == 1000
    assert result.mode == 0o775
    assert not result.read_only


@pytest.mark.parametrize(
    "path",
    [
        "/mnt",
        "/mnt/sdk",
        "/root",
        "/root/.cache/dir",
        "/run/user/1001",
        "/run/user/1001/sdk",
    ],
)
def test_mount_plug_defaults_root(path: str):
    plug = {"interface": "mount", "workshop-target": path}

    result = MountPlug.unmarshal(plug)
    assert result.uid == 0
    assert result.gid == 0
    assert result.mode == 0o755
    assert not result.read_only


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, False),
        (True, True),
        (False, False),
        ("true", True),
        ("false", False),
        ("TRUE", True),
        ("TrUe", True),
        (1, True),
        (0, False),
        (1.0, True),
        (0.0, False),
    ],
)
def test_mount_plug_read_only_valid(
    *, value: bool | float | str | None, expected: bool
):
    plug = {"interface": "mount", "workshop-target": "/data", "read-only": value}
    if value is None:
        del plug["read-only"]

    assert MountPlug.unmarshal(plug).read_only == expected


@pytest.mark.parametrize("value", ["invalid-value", 2])
def test_mount_plug_read_only_invalid(value: int | str):
    plug = {"interface": "mount", "workshop-target": "/data", "read-only": value}
    with pytest.raises(ValidationError):
        MountPlug.unmarshal(plug)


plugs_adapter: TypeAdapter[Plugs] = TypeAdapter(Plugs)


def test_implicit_interfaces():
    plugs = yaml.safe_load("""
        camera:
        desktop: desktop
        gpu:
        ssh-agent: 'ssh-agent'
    """)

    expected = {
        "camera": CameraPlug(interface="camera"),
        "desktop": DesktopPlug(interface="desktop"),
        "gpu": GPUPlug(interface="gpu"),
        "ssh-agent": SSHAgentPlug(interface="ssh-agent"),
    }

    assert plugs_adapter.validate_python(plugs) == expected


def test_interface_policies():
    with pytest.raises(
        ValidationError,
        match="ssh-agent interface plugs must be named 'ssh-agent'",
    ):
        plugs_adapter.validate_python({"foo": {"interface": "ssh-agent"}})


part_adapter: TypeAdapter[Part] = TypeAdapter(Part)


def test_part_inherits_constraints():
    with pytest.raises(ValidationError):
        part_adapter.validate_python({})


def test_part_stage_packages_prohibited():
    with pytest.raises(
        ValidationError,
        match="'stage-packages' are not supported by SDKcraft",
    ):
        part_adapter.validate_python(
            {"plugin": "nil", "stage-packages": ["python3-apt"]}
        )


def test_part_stage_snaps_prohibited():
    with pytest.raises(
        ValidationError,
        match="'stage-snaps' are not supported by SDKcraft",
    ):
        part_adapter.validate_python({"plugin": "nil", "stage-snaps": ["shellcheck"]})
