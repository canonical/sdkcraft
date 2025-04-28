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
"""Services for SDKcraft."""

from __future__ import annotations

import pathlib
import shutil
import tarfile
from datetime import datetime, timezone
from typing import cast

from craft_application import AppMetadata, services
from overrides import override  # pyright: ignore[reportUnknownVariableType]

from sdkcraft import models


class Package(services.PackageService):
    """Package service for Sdkcraft."""

    def __init__(
        self,
        app: AppMetadata,
        project: models.Project,
        services: services.ServiceFactory,
        started_at: datetime | None = None,
    ) -> None:
        super().__init__(app, services, project=project)

        if started_at is None:
            started_at = datetime.now(timezone.utc)
        self._started_at = started_at

    @override
    def pack(self, prime_dir: pathlib.Path, dest: pathlib.Path) -> list[pathlib.Path]:
        """Create one or more packages as appropriate.

        :param dest: Directory into which to write the package(s).
        :returns: A list of paths to created packages.
        """
        binary_package_name = f"{self._project.name}.sdk"
        with tarfile.open(dest / binary_package_name, mode="w:xz") as tar:
            tar.dereference = True
            for entry in sorted(prime_dir.iterdir()):
                tar.add(entry, arcname=entry.name, recursive=True)
        return [dest / binary_package_name]

    @property
    @override
    def metadata(self) -> models.Metadata:
        """Generate the sdk.yaml model for the output file."""
        project = cast(models.Project, self._project)
        return models.Metadata(
            **project.model_dump(
                include={
                    "name",
                    "title",
                    "version",
                    "summary",
                    "description",
                    "base",
                    "contact",
                    "issues",
                    "source_code",
                    "license",
                    "plugs",
                    "slots",
                },
                by_alias=True,
                exclude_unset=True,
            ),
            sdkcraft_started_at=datetime_as_utc_str(self._started_at),
        )

    @override
    def write_metadata(self, path: pathlib.Path) -> None:
        """Write the resulting metadata into the given prime directory.

        :param path: The path to the prime directory.
        """
        meta = path / "meta"
        meta.mkdir(parents=True, exist_ok=True)
        self.metadata.to_yaml_file(meta / "sdk.yaml")

        dirs = self._services.lifecycle.project_info.dirs
        hooks_dir = dirs.project_dir / "hooks"
        if hooks_dir.is_dir():
            shutil.copytree(hooks_dir, path / "sdk" / "hooks", dirs_exist_ok=True)


def datetime_as_utc_str(dt: datetime) -> str:
    """Convert to UTC and format as ISO 8601.

    :param dt: A timezone-aware date and time.
    """
    if dt.tzinfo is None:
        raise NotImplementedError("timezone required")

    # Append Z because Go does not recognize +00:00 as UTC.
    return dt.astimezone(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
