# This file is part of sdkcraft.
#
# Copyright 2024 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranties of MERCHANTABILITY,
# SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
"""SDKcraft project service."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from craft_application import AppMetadata, ServiceFactory, services
from craft_application.errors import ProjectFileMissingError

if TYPE_CHECKING:
    from pathlib import Path


class ProjectService(services.ProjectService):
    """A service for handling access to the project."""

    __sdkcraft_project_file_path: Path | None

    @override
    def __init__(
        self, app: AppMetadata, services: ServiceFactory, *, project_dir: Path
    ) -> None:
        super().__init__(app, services, project_dir=project_dir)
        self.__sdkcraft_project_file_path = None

    @override
    def resolve_project_file_path(self) -> Path:
        """Get the path to the project file from the root project directory."""
        if not self.__sdkcraft_project_file_path:
            self.__sdkcraft_project_file_path = self._resolve_project_file_path()
        return self.__sdkcraft_project_file_path

    def _resolve_project_file_path(self) -> Path:
        try:
            return super().resolve_project_file_path()
        except ProjectFileMissingError:
            try:
                return (self._project_dir / ".sdkcraft.yaml").resolve(strict=True)
            except FileNotFoundError:
                pass

            try:
                return (self._project_dir / "sdk.yaml").resolve(strict=True)
            except FileNotFoundError:
                pass

            try:
                return (self._project_dir / ".sdk.yaml").resolve(strict=True)
            except FileNotFoundError:
                pass

            raise
