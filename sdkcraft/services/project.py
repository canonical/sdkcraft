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

import os
import pathlib

from craft_application import AppMetadata, ServiceFactory, errors, services
from craft_cli import emit
from typing_extensions import override


class Project(services.ProjectService):
    """A service for handling access to the project."""

    __sdk_file_path: pathlib.Path | None

    def __init__(
        self, app: AppMetadata, services: ServiceFactory, *, project_dir: pathlib.Path
    ) -> None:
        super().__init__(app, services, project_dir=project_dir)
        self.__sdk_file_path = None

    @override
    def resolve_project_file_path(self) -> pathlib.Path:
        """Get the path to the project file from the root project directory."""
        if self.__sdk_file_path:
            return self.__sdk_file_path

        if not self._project_dir.is_dir():
            if not self._project_dir.exists():
                raise errors.ProjectDirectoryMissingError(self._project_dir)
            raise errors.ProjectDirectoryTypeError(self._project_dir)

        path = _resolve_project_file_path(self._project_dir)
        emit.trace(f"Project file found at {path}")
        self.__sdk_file_path = path
        return path


def _resolve_project_file_path(project_dir: pathlib.Path) -> pathlib.Path:
    try:
        return (project_dir / "sdk.yaml").resolve(strict=True)
    except FileNotFoundError:
        pass

    try:
        return (project_dir / ".sdk.yaml").resolve(strict=True)
    except FileNotFoundError:
        pass

    raise errors.ProjectFileMissingError(
        f"Project file 'sdk.yaml' not found in '{project_dir}'.",
        details="The project file could not be found.",
        resolution="Ensure the project file exists.",
        retcode=os.EX_NOINPUT,
    )
