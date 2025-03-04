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

import pytest
from craft_application import models
from pydantic import TypeAdapter, ValidationError
from sdkcraft.errors import SdkcraftError
from sdkcraft.models.project import Part, Project

default = Project(
    name="my-project",
    version="git",
    title="Sample",
    summary="A sample project",
    description="description",
    base="ubuntu@22.04",
    contact="contact@canonical.com",
    issues="https://github.com/canonical/sdks/issues",
    source_code=None,
    adopt_info=None,
    package_repositories=None,
    platforms={
        "amd64": models.Platform(
            build_for=["amd64"],
            build_on=["amd64"],
        ),
        "riscv64": models.Platform(
            build_on=["amd64", "arm64"],
            build_for=["riscv64"],
        ),
    },
    license="gplv3",
    parts={},
    plugs={},
    slots={},
)


@pytest.mark.parametrize(
    ("obj", "expected"),
    [
        (
            {
                "name": "my-project",
                "version": "git",
                "summary": "A sample project",
                "base": "ubuntu@22.04",
                "title": "Sample",
                "description": "description",
                "contact": "contact@canonical.com",
                "issues": "https://github.com/canonical/sdks/issues",
                "platforms": {
                    "amd64": {"build-for": ["amd64"], "build-on": ["amd64"]},
                    "riscv64": {
                        "build-on": ["amd64", "arm64"],
                        "build-for": ["riscv64"],
                    },
                },
                "license": "gplv3",
                "parts": {},
                "plugs": {},
                "slots": {},
            },
            default,
        ),
    ],
)
def test_project_create_valid(obj, expected):
    assert Project.model_validate(obj) == expected


def test_project_plugs():
    valid_plugs = {
        "mount": {"interface": "mount", "workshop-target": "/data"},
        "randomg": {"interface": "existing"},
        "mount2": {"workshop-target": "/data"},
        "mount_mode_true": {
            "interface": "mount",
            "workshop-target": "/data",
            "read-only": True,
        },
        "mount_mode_false": {
            "interface": "mount",
            "workshop-target": "/data",
            "read-only": False,
        },
        "mount_mode_string_true": {
            "interface": "mount",
            "workshop-target": "/data",
            "read-only": "true",
        },
        "mount_mode_string_false": {
            "interface": "mount",
            "workshop-target": "/data",
            "read-only": "false",
        },
        "mount_mode_string_true_caps": {
            "interface": "mount",
            "workshop-target": "/data",
            "read-only": "TRUE",
        },
        "mount_mode_string_true_mixed": {
            "interface": "mount",
            "workshop-target": "/data",
            "read-only": "TrUe",
        },
    }
    try:
        default._validate_plugs(valid_plugs)
    except ValueError as e:
        pytest.fail(reason=f"unexpected exception {e}")

    no_target = {
        "mount": {"interface": "mount"},
    }
    with pytest.raises(
        SdkcraftError,
        match="MountPlug 'mount' must have a 'workshop-target' parameter.",
    ):
        default._validate_plugs(no_target)

    incorrect_type = {"mount": ["interface", "mount"]}
    with pytest.raises(SdkcraftError, match="cannot be a list"):
        default._validate_plugs(incorrect_type)

    incorrect_mode = {
        "incorrect_mode": {
            "interface": "mount",
            "workshop-target": "/data",
            "read-only": "invalid-value",
        }
    }
    with pytest.raises(
        SdkcraftError,
        match="Value 'invalid-value' in optional parameter 'read-only' for MountPlug 'incorrect_mode' is invalid.",
    ):
        default._validate_plugs(incorrect_mode)


def test_project_slots():
    valid_slots = {
        "mount-slot": {"interface": "mount", "workshop-source": "/data"},
        "random-slot-1": {"interface": "xxx"},
        "random-slot-2": {"yyy": "zzz"},
    }
    try:
        default._validate_slots(valid_slots)
    except ValueError as e:
        pytest.fail(reason=f"unexpected exception {e}")

    no_source = {
        "try_mount_1": {"interface": "mount"},
    }
    with pytest.raises(
        SdkcraftError,
        match="MountSlot 'try_mount_1' must have a 'workshop-source' string parameter.",
    ):
        default._validate_slots(no_source)

    incorrect_type = {
        "try_mount_2": {"interface": "mount", "workshop-source": 123},
    }
    with pytest.raises(
        SdkcraftError,
        match="MountSlot 'try_mount_2' must have a 'workshop-source' string parameter.",
    ):
        default._validate_slots(incorrect_type)


part_adapter = TypeAdapter(Part)


def test_part_inherits_constraints():
    with pytest.raises(ValidationError):
        part_adapter.validate_python({})


def test_part_stage_packages_prohibited():
    with pytest.raises(
        ValidationError,
        match="'stage-packages' are not supported by sdkcraft",
    ):
        part_adapter.validate_python(
            {"plugin": "nil", "stage-packages": ["python3-apt"]}
        )


def test_part_stage_snaps_prohibited():
    with pytest.raises(
        ValidationError,
        match="'stage-snaps' are not supported by sdkcraft",
    ):
        part_adapter.validate_python({"plugin": "nil", "stage-snaps": ["shellcheck"]})
