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
"""Services for sdkcraft."""

from __future__ import annotations

import pathlib
import tarfile
from pathlib import Path
from typing import cast

import craft_parts
from craft_application import AppMetadata, services
from overrides import override

from sdkcraft import models


class Package(services.PackageService):
    """Package service for Sdkcraft."""

    def __init__(
        self,
        app: AppMetadata,
        project: models.Project,
        services: services.ServiceFactory,
    ) -> None:
        super().__init__(app, services, project=project)

    def _pack_hooks(self, arch: tarfile.TarFile) -> None:
        """Add provided hooks to the package."""
        dirs = craft_parts.ProjectDirs(work_dir=Path("/root"))
        hooks_dir = dirs.project_dir / "hooks"
        # the list of supported hooks
        hooks = ["setup-base", "save-state", "restore-state", "check-health"]

        for name in hooks:
            hook = hooks_dir / name
            if hook.is_file():
                arch.add(hook, arcname=Path("sdk") / "hooks" / name)

    @override
    def pack(self, prime_dir: pathlib.Path, dest: pathlib.Path) -> list[pathlib.Path]:
        """Create one or more packages as appropriate.

        :param dest: Directory into which to write the package(s).
        :returns: A list of paths to created packages.
        """
        self.write_metadata(prime_dir)

        binary_package_name = f"{self._project.name}.sdk"
        with tarfile.open(dest / binary_package_name, mode="w:xz") as tar:
            tar.dereference=True
            tar.add(prime_dir, arcname=".", recursive=True)
            self._pack_hooks(tar)
        return [dest / binary_package_name]

    @property
    @override
    def metadata(self) -> models.Metadata:
        """Generate the sdkcraft.yaml model for the output file."""
        project = cast(models.Project, self._project)
        return models.Metadata(
            **project.model_dump(
                include={
                    "name",
                    "base",
                    "version",
                    "title",
                    "summary",
                    "license",
                    "description",
                    "contact",
                    "issues",
                    "source_code",
                    "plugs",
                },
                exclude_unset=True,
            )
        )

    @override
    def write_metadata(self, path: pathlib.Path) -> None:
        """Write the resulting metadata into the given prime directory.

        :param path: The path to the prime directory.
        """
        path = path / "meta"
        path.mkdir(parents=True, exist_ok=True)
        self.metadata.to_yaml_file(path / "sdk.yaml")
