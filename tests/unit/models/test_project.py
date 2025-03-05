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
from sdkcraft.models.project import MountPlug, Part, Project

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
            },
            default,
        ),
    ],
)
def test_project_create_valid(obj, expected):
    assert Project.unmarshal(obj) == expected


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
def test_mount_plug_read_only_valid(value, expected):
    plug = {"interface": "mount", "workshop-target": "/data", "read-only": value}
    if value is None:
        del plug["read-only"]

    assert MountPlug.unmarshal(plug).read_only == expected


@pytest.mark.parametrize("value", ["invalid-value", 2])
def test_mount_plug_read_only_invalid(value):
    plug = {"interface": "mount", "workshop-target": "/data", "read-only": value}
    with pytest.raises(ValidationError):
        MountPlug.unmarshal(plug)


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
