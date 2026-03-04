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

from os import EX_NOINPUT
from typing import TYPE_CHECKING, cast, override

from craft_application import AppMetadata, ServiceFactory, services
from craft_application.errors import ProjectFileMissingError

from sdkcraft.models import MarkedLoader, MarkedProject, Project

if TYPE_CHECKING:
    from pathlib import Path

    from craft_platforms import BuildInfo


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

            raise ProjectFileMissingError(
                f"Project file {self.project_file_name!r} not found in {str(self._project_dir)!r}.",
                resolution="Run 'sdkcraft init' to generate a sample project.",
                reportable=False,
                logpath_report=False,
                retcode=EX_NOINPUT,
            )

    def get_with_base(self, build_info: BuildInfo) -> Project:
        """Get the project data specialized for the given platform."""
        project = cast(Project, self.get())
        # Multi-base projects specify the base (not build-base) for each platform.
        if not project.base and not project.build_base:
            project = project.model_copy(update={"base": str(build_info.build_base)})

        return project

    def get_marked(self) -> MarkedProject:
        """Get the project data structure with associated line numbers."""
        path = self.resolve_project_file_path()
        with path.open() as f:
            marked = MarkedLoader.load(f)

        return MarkedProject.unmarshal(
            marked | {"path": path.relative_to(self._project_dir), "abspath": path}
        )
