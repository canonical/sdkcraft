# Copyright 2024 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Lifecycle commands for SDKcraft."""

import errno
import os
import shutil
import subprocess
import textwrap
from argparse import Namespace
from collections.abc import Iterable, Iterator
from contextlib import ExitStack
from hashlib import file_digest, sha3_384
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import platformdirs
from craft_application import PackageService
from craft_application.commands import lifecycle
from craft_application.util import is_managed_mode
from craft_cli import CraftError, emit
from craft_platforms import BuildInfo
from typing_extensions import override


class PackCommand(lifecycle.PackCommand):
    """Command to pack the final artifact."""

    @override
    def _is_already_packed(self) -> bool:
        if not super()._is_already_packed():
            return False

        pack_time = self._get_packed_file_list_timestamp()
        if pack_time is None:
            return False

        project_file = self._services.get("project").resolve_project_file_path()
        if project_file.stat().st_mtime_ns >= pack_time:
            return False

        dirs = self._services.get("lifecycle").project_info.dirs
        hooks = dirs.project_dir / "hooks"
        if hooks.is_dir():
            hooks_time = max(_walk_mtimes(hooks))
        else:
            # Hooks directory may have been deleted since last pack. Checking the
            # parent directory is coarse, but most SDKs have at least one hook.
            hooks_time = hooks.parent.stat().st_mtime_ns

        return hooks_time < pack_time


def _walk_mtimes(path: Path) -> Iterator[int]:
    yield path.stat().st_mtime_ns
    with os.scandir(path) as entries:
        for entry in entries:
            time = entry.stat(follow_symlinks=False).st_mtime_ns
            if entry.is_symlink() or entry.is_file():
                yield time
            elif entry.is_dir():
                yield time
                yield from _walk_mtimes(path / entry.name)


class TryCommand(PackCommand):
    """Try out an SDKcraft project."""

    name = "try"
    help_msg = "Try SDKs before publishing"
    overview = textwrap.dedent(
        """
        Pack the SDK and copy it to the Workshop try area.
        """
    )

    @override
    def _run(
        self, parsed_args: Namespace, step_name: str | None = None, **kwargs: Any
    ) -> None:
        super()._run(parsed_args=parsed_args, step_name=step_name, **kwargs)
        if is_managed_mode():
            # If we're in managed mode, we just need to pack.
            return

        build_plan = self._services.get("build_plan").plan()
        package = self._services.get("package")
        artifacts = [_artifact(package, build_info) for build_info in build_plan]

        project = self._services.get("project").get()
        self._try(project.name, artifacts)

    def _try(self, name: str, artifacts: Iterable[Path]) -> None:
        try_area = platformdirs.user_data_path("workshop") / "sdk"
        try_area.mkdir(parents=True, exist_ok=True)

        with ExitStack() as stack:
            target = Path(stack.enter_context(TemporaryDirectory(dir=try_area)))

            for artifact in artifacts:
                emit.progress(f"Copying {artifact.name}...")
                artifact_path = target / artifact.name
                shutil.copy2(artifact, artifact_path)

                with artifact_path.open("rb") as f:
                    sha3_digest = file_digest(f, sha3_384).hexdigest()
                sha3_path = artifact_path.with_name(artifact.name + ".sha3-384")
                sha3_path.write_text(sha3_digest + "\n")

                meta_path = artifact_path.with_name(artifact.name + ".yaml")
                with meta_path.open("w") as meta:
                    subprocess.run(
                        [
                            "tar",
                            "--extract",
                            "--to-stdout",
                            "--force-local",
                            f"--file={artifact_path}",
                            "meta/sdk.yaml",
                        ],
                        check=True,
                        stdout=meta,
                        stderr=subprocess.PIPE,
                        text=True,
                    )

            _rename(target, try_area / name)
            stack.pop_all()

        emit.progress("Copied SDKs to try area.", permanent=True)


def _artifact(package: PackageService, build_info: BuildInfo) -> Path:
    pack_state = package.read_state(build_info.platform)
    if pack_state.artifact is None:
        raise CraftError(
            f"No artifact was packed for platform '{build_info.platform}'",
            resolution=f"Ensure platform '{build_info.platform}' packs correctly.",
        )
    return pack_state.artifact


def _rename(source: Path, target: Path) -> None:
    try:
        source.rename(target)
    except OSError as e:
        if e.errno != errno.ENOTEMPTY:
            raise
    else:
        return

    # Poor approximation of `atomicswap.swap`.
    with TemporaryDirectory(dir=target.parent) as cleanup:
        target.replace(cleanup)
        source.rename(target)
