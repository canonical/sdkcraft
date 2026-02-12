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
"""Tests for linters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sdkcraft.linters.interfaces import InterfaceCheck
from sdkcraft.models import LinterIssue, LinterResult, Location

if TYPE_CHECKING:
    import pytest
    from sdkcraft.services import ProjectService

PROJECT_YAML = """\
name: default
summary: default project
plugs:
  venv:
    interface: mount
    workshop-target: $SDK/venv
    read-only: false
  gpu:
  ssh-agent: ssh-agent
  cache:
    interface: mount
    workshop-target: /home/workshop/.cache/default
slots:
  config:
    interface: mount
    workshop-source: /var/lib/workshop/sdk/default/source
"""


def test_interface_check(
    project_service: ProjectService, tmp_path_factory: pytest.TempPathFactory
):
    project_file = project_service.resolve_project_file_path()
    project_file.write_text(PROJECT_YAML)
    project = project_service.get_marked()
    assert project.abspath == project_file

    workshop_target = LinterIssue(
        linter="mount-interface",
        result=LinterResult.ERROR,
        message="workshop-target '$SDK/venv' not found for 'venv' mount plug",
        path=project.path,
        abspath=project.abspath,
        location=Location(line=6, end_line=6, column=22, end_column=30),
    )

    workshop_source = LinterIssue(
        linter="mount-interface",
        result=LinterResult.ERROR,
        message="workshop-source '$SDK/source' not found for 'config' mount slot",
        path=project.path,
        abspath=project.abspath,
        location=Location(line=16, end_line=16, column=22, end_column=57),
    )

    prime_dir = tmp_path_factory.mktemp("prime")
    issues = InterfaceCheck().run(prime_dir, project)
    issues.sort(key=lambda issue: issue.location.line or -1)
    assert issues == [workshop_target, workshop_source]

    (prime_dir / "venv").mkdir()
    issues = InterfaceCheck().run(prime_dir, project)
    assert issues == [workshop_source]

    (prime_dir / "source").mkdir()
    issues = InterfaceCheck().run(prime_dir, project)
    assert issues == []
