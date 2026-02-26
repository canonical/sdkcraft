#  This file is part of sdkcraft.
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
"""SDKcraft init service."""

from __future__ import annotations

from typing import override

from craft_application import services
from craft_application.errors import InitError
from craft_application.util.error_formatting import format_pydantic_errors
from pydantic import TypeAdapter, ValidationError

from sdkcraft.models.constraints import ProjectName


class InitService(services.InitService):
    """Service class for initializing a project."""

    @override
    def validate_project_name(self, name: str, *, use_default: bool = False) -> str:
        try:
            TypeAdapter(ProjectName).validate_python(name)
        except ValidationError as e:
            if use_default:
                return self._default_name

            message = format_pydantic_errors(e.errors(), file_name="name")
            raise InitError(message) from None

        return name
