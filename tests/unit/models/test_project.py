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
from craft_application.models import ProjectName, ProjectTitle, SummaryStr, VersionStr
from sdkcraft.errors import SdkcraftError
from sdkcraft.models import project

default = project.Project(
                name=ProjectName("my-project"),
                version=VersionStr("git"),
                title=ProjectTitle("Sample"),
                summary=SummaryStr("A sample project"),
                description="description",
                base="ubuntu@22.04",
                contact="contact@canonical.com",
                issues="https://github.com/canonical/sdk-store/issues",
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
                "issues": "https://github.com/canonical/sdk-store/issues",
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
            },
            default,
        ),
    ],
)
def test_project_create_valid(obj, expected):
    assert project.Project.parse_obj(obj) == expected


def test_project_stage_packages_prohibited():
    part_packages = {"plugin": "nil", "stage-packages": ["python3-apt"]}
    with pytest.raises(NotImplementedError):
        default._validate_parts(part_packages)

    part_snaps = {"plugin": "nil", "stage-snaps": ["shellcheck"]}
    with pytest.raises(NotImplementedError):
        default._validate_parts(part_snaps)


def test_project_plugs():
    valid_plugs = {
        "mount": {"interface": "mount", "workshop-target": "/data"},
        "randomg": {"interface": "existing"},
        "mount2": {"workshop-target": "/data"},
    }
    try:
        default._validate_plugs(valid_plugs)
    except ValueError as e:
        pytest.fail(reason=f"unexpected exception {e}")

    no_target = {
        "mount": {"interface": "mount"},
    }
    with pytest.raises(
        SdkcraftError, match="MountPlug 'mount' must have a 'workshop-target' parameter."
    ):
        default._validate_plugs(no_target)

    incorrect_type = {"mount": ["interface", "mount"]}
    with pytest.raises(SdkcraftError, match="cannot be a list"):
        default._validate_plugs(incorrect_type)


def test_project_reserved_name_forbidden():
    with pytest.raises(
        SdkcraftError,
        match="'agent' is a reserved SDK name, please choose another name.",
    ):
        project.Project.parse_obj(
            {
                "name": "agent",
                "version": "git",
                "summary": "A sample project",
                "base": "ubuntu@22.04",
                "platforms": {
                    "amd64": None,
                    "riscv64": {"build-on": ["amd64", "arm64"]},
                },
                "license": "gplv3",
                "parts": {},
            }
        )
