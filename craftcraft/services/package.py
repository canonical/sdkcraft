#  This file is part of craftcraft.
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
"""Services for craftcraft."""
from __future__ import annotations

import pathlib
import tarfile
from typing import cast

from craft_application import AppMetadata, services
from overrides import override

from craftcraft import models


class Package(services.PackageService):
    """Package service for Craftcraft."""

    def __init__(
        self,
        app: AppMetadata,
        project: models.Project,
        services: services.ServiceFactory,
        *,
        platform: str | None,
        build_for: str,
    ) -> None:
        super().__init__(app, services, project=project)
        self._platform = platform
        self._build_for = build_for

    @override
    def pack(self, prime_dir: pathlib.Path, dest: pathlib.Path) -> list[pathlib.Path]:
        """Create one or more packages as appropriate.

        :param dest: Directory into which to write the package(s).
        :returns: A list of paths to created packages.
        """
        self.write_metadata(prime_dir)

        binary_package_name = f"{self._project.name}_{self._project.version}.tar.xz"
        with tarfile.open(dest / binary_package_name, mode="w:xz") as tar:
            tar.add(prime_dir, arcname=".", recursive=True)
            tar.add(prime_dir / "metadata.yaml", arcname="metadata.yaml")
        return [dest / binary_package_name]

    @property
    @override
    def metadata(self) -> models.Metadata:
        """Generate the metadata.yaml model for the output file."""
        project = cast(models.Project, self._project)
        return models.Metadata(**project.dict())

    @override
    def write_metadata(self, path: pathlib.Path) -> None:
        """Write the resulting metadata into the given prime directory.

        :param path: The path to the prime directory.
        """
        path = path / "meta"
        path.mkdir(parents=True, exist_ok=True)
        self.metadata.to_yaml_file(path / "metadata.yaml")
