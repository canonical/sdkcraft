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
from sdkcraft.models.constraints import ProjectName

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
