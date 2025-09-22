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
"""SDKcraft lifecycle service."""

from __future__ import annotations

from pathlib import Path
from typing import override

from craft_application import services
from craft_application.errors import PartsLifecycleError
from craft_application.util import get_parallel_build_count
from craft_cli import emit
from craft_parts import PartsError

from sdkcraft.lifecycle_manager import LifecycleManager


class LifecycleService(services.LifecycleService):
    """Lifecycle service for SDKcraft."""

    @override
    def _init_lifecycle_manager(self) -> LifecycleManager:
        """Create and return the Lifecycle manager.

        An application may override this method if needed if the lifecycle
        manager needs to be called differently.
        """
        emit.debug(f"Initialising lifecycle manager in {self._work_dir}")
        emit.trace(f"Lifecycle: {repr(self)}")

        project_service = self._services.get("project")
        build_for = self._get_build_for()

        if self._project.package_repositories:
            self._manager_kwargs["package_repositories"] = (
                self._project.package_repositories
            )

        source_ignore_patterns = [
            ".craft",  # in case of unmanaged lifecycle run
            *self._app.source_ignore_patterns,
        ]

        if Path("spread/.extension").exists():
            # Ignore spread.yaml and spread to prevent repulling sources
            # when test files are changed.
            source_ignore_patterns.extend(["spread.yaml", "spread"])

        try:
            return LifecycleManager(
                {"parts": self._project.parts},
                application_name=self._app.name,
                arch=build_for,
                cache_dir=self._cache_dir,
                work_dir=self._work_dir,
                ignore_local_sources=source_ignore_patterns,
                parallel_build_count=get_parallel_build_count(self._app.name),
                project_vars=project_service.project_vars,
                track_stage_packages=True,
                partitions=project_service.partitions,
                **self._manager_kwargs,
            )
        except PartsError as err:
            raise PartsLifecycleError.from_parts_error(err) from err
