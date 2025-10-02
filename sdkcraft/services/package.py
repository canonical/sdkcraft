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
"""SDKcraft package service."""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
from datetime import datetime, timezone
from typing import override

from craft_application import AppMetadata, services
from craft_application.models import Project

from sdkcraft import models


class PackageService(services.PackageService):
    """Package service for SDKcraft."""

    def __init__(
        self,
        app: AppMetadata,
        services: services.ServiceFactory,
        started_at: datetime | None = None,
    ) -> None:
        super().__init__(app, services)

        if started_at is None:
            started_at = datetime.now(timezone.utc)
        self._started_at = started_at

    @override
    def pack(self, prime_dir: pathlib.Path, dest: pathlib.Path) -> list[pathlib.Path]:
        """Create one or more packages as appropriate.

        :param dest: Directory into which to write the package(s).
        :returns: A list of paths to created packages.
        """
        project, arch = self._project_and_arch()

        components = [project.name, arch]
        if project.base:
            components.append(project.base)
        sdk = dest / ("_".join(components) + ".sdk")

        sdk.unlink(missing_ok=True)
        names = (p.name for p in sorted(prime_dir.iterdir()))
        subprocess.run(
            [
                "tar",
                "--create",
                "--format=posix",
                "--use-compress-program=zstd -10 --threads=0",
                # Restrict to rwxr-xr-x for security and reproducibility.
                "--mode=a-st,go-w",
                "--owner=root:0",
                "--group=root:0",
                f"--mtime={datetime_as_utc_str(self._started_at)}",
                "--sort=name",
                "--force-local",
                f"--file={sdk}",
                f"--directory={prime_dir}",
                "--",
                *names,
            ],
            check=True,
        )

        return [sdk]

    @property
    @override
    def metadata(self) -> models.Metadata:
        """Generate the sdk.yaml model for the output file."""
        project, arch = self._project_and_arch()
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
            architecture=arch,
            sdkcraft_started_at=datetime_as_utc_str(self._started_at),
        )

    def _project_and_arch(self) -> tuple[Project, str]:
        # Multi-base projects specify the base (not build-base) for each platform.
        project = self._project
        build_info = self._build_info
        if not project.base and not project.build_base:
            project = project.model_copy(update={"base": str(build_info.build_base)})

        return project, str(build_info.build_for)

    @override
    def write_metadata(self, path: pathlib.Path) -> None:
        """Write the resulting metadata into the given prime directory.

        :param path: The path to the prime directory.
        """
        meta = path / "meta"
        meta.mkdir(parents=True, exist_ok=True)
        self.metadata.to_yaml_file(meta / "sdk.yaml")

        dirs = self._services.get("lifecycle").project_info.dirs
        hooks_source = dirs.project_dir / "hooks"
        if hooks_source.is_dir():
            hooks_target = path / "sdk" / "hooks"
            if hooks_target.is_dir():
                shutil.rmtree(hooks_target)
            else:
                hooks_target.parent.mkdir(exist_ok=True)
            copytree(hooks_source, hooks_target)


def datetime_as_utc_str(dt: datetime) -> str:
    """Convert to UTC and format as ISO 8601.

    :param dt: A timezone-aware date and time.
    """
    if dt.tzinfo is None:
        raise NotImplementedError("timezone required")

    # Append Z because Go does not recognize +00:00 as UTC.
    return dt.astimezone(timezone.utc).replace(tzinfo=None).isoformat() + "Z"


def copytree(source: os.PathLike[str], target: pathlib.Path) -> None:
    """Recursively copy a directory tree.

    Preserves metadata and symlinks, but ignores other non-regular files.

    :param source: Directory to copy.
    :param target: Copy to create.
    """
    target.mkdir()

    with os.scandir(source) as entries:
        for entry in entries:
            path = target / entry.name
            if entry.is_symlink():
                link = pathlib.Path(entry).readlink()
                path.symlink_to(link)
                shutil.copystat(entry, path, follow_symlinks=False)
            elif entry.is_dir():
                copytree(entry, path)
            elif entry.is_file():
                shutil.copy2(entry, path)

    shutil.copystat(source, target)
