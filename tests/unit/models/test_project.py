# This file is part of craftcraft.
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
from craft_providers import bases
from craftcraft.models import project, util


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("amd64", [util.Architecture.AMD64]),
        (["riscv64", "arm64"], [util.Architecture.RISCV64, util.Architecture.ARM64]),
        (util.Architecture.ARM64, [util.Architecture.ARM64]),
        ([util.Architecture.S390X], [util.Architecture.S390X]),
    ],
)
def test_platform_vectorise(value, expected):
    assert project.Platform.vectorise(value) == expected


@pytest.mark.parametrize(
    ("platforms", "expected"),
    [
        (
            {"amd64": None},
            {
                "amd64": {
                    "build-on": [util.Architecture.AMD64],
                    "build-for": [util.Architecture.AMD64],
                }
            },
        ),
        (
            {"arbitrary platform name": {"build-on": "amd64", "build-for": "arm64"}},
            {"arbitrary platform name": {"build-on": "amd64", "build-for": "arm64"}},
        ),
        (
            {"riscv64": {"build-on": ["amd64", "arm64"]}},
            {
                "riscv64": {
                    "build-on": ["amd64", "arm64"],
                    "build-for": [util.Architecture.RISCV64],
                }
            },
        ),
    ],
)
def test_project_pre_parse_platforms(platforms, expected):
    assert project.Project.pre_parse_platforms(platforms) == expected


@pytest.mark.parametrize(
    ("obj", "expected"),
    [
        (
            {
                "name": "my-project",
                "version": "git",
                "summary": "A sample project",
                "base": "ubuntu@22.04",
                "platforms": {
                    "amd64": None,
                    "riscv64": {"build-on": ["amd64", "arm64"]},
                },
                "license": "gplv3",
                "parts": {},
            },
            project.Project(
                name="my-project",
                version="git",
                summary="A sample project",
                base=util.Base.JAMMY,
                platforms={
                    "amd64": project.Platform(
                        build_for=[util.Architecture.AMD64],
                        build_on=[util.Architecture.AMD64],
                    ),
                    "riscv64": project.Platform(
                        build_on=[util.Architecture.AMD64, util.Architecture.ARM64],
                        build_for=[util.Architecture.RISCV64],
                    ),
                },
                license="gplv3",
                parts={},
            ),
        ),
    ],
)
def test_project_create_valid(obj, expected):
    assert project.Project.parse_obj(obj) == expected


@pytest.mark.parametrize(
    ("project", "expected"),
    [
        (
            project.Project(
                name="my-project",
                version="git",
                summary="A sample project",
                base=util.Base.JAMMY,
                platforms={
                    "amd64": project.Platform(
                        build_for=[util.Architecture.AMD64],
                        build_on=[util.Architecture.AMD64],
                    ),
                    "riscv64": project.Platform(
                        build_on=[util.Architecture.AMD64, util.Architecture.ARM64],
                        build_for=[util.Architecture.RISCV64],
                    ),
                },
                license="gplv3",
                parts={},
            ),
            [
                models.BuildInfo(
                    "amd64",
                    util.Architecture.AMD64.value,
                    util.Architecture.AMD64.value,
                    bases.BaseName("ubuntu", "22.04"),
                ),
                models.BuildInfo(
                    "riscv64",
                    util.Architecture.AMD64.value,
                    util.Architecture.RISCV64.value,
                    bases.BaseName("ubuntu", "22.04"),
                ),
                models.BuildInfo(
                    "riscv64",
                    util.Architecture.ARM64.value,
                    util.Architecture.RISCV64.value,
                    bases.BaseName("ubuntu", "22.04"),
                ),
            ],
        ),
    ],
)
def test_project_get_build_plan(project, expected):
    assert project.get_build_plan() == expected
