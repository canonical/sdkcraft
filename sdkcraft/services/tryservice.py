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
"""SDKcraft try service."""

from __future__ import annotations

import shutil
import subprocess
from contextlib import ExitStack, suppress
from errno import ENOTEMPTY
from hashlib import file_digest, sha3_384
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from craft_application import AppService
from craft_cli import emit

from sdkcraft import env

if TYPE_CHECKING:
    from collections.abc import Mapping


class TryService(AppService):
    """Try out SDKs built with SDKcraft."""

    def copy(
        self,
        name: str,
        artifacts: Mapping[str, Path],
        try_area: Path | None = None,
        *,
        progress: bool = False,
    ) -> None:
        """Copy the given artifacts into the named subdirectory of the try area."""
        if try_area is None:
            try_area = env.user_data_path() / "workshop" / "try"
            try_area.mkdir(parents=True, exist_ok=True)

        with ExitStack() as stack:
            temp_dir = TemporaryDirectory(prefix="tmp.", dir=try_area, delete=False)
            stack.callback(temp_dir.cleanup)
            target = Path(temp_dir.name)

            for artifact in artifacts.values():
                _copy_to(artifact, target, progress=progress)

            _rename(target, try_area / name)
            stack.pop_all()

        if progress:
            platforms = ", ".join(artifacts.keys())
            try_name = f"try-{name}"
            command = "workshop refresh"

            emit.progress(
                f"Copied {name!r} SDK ({platforms}) to the try area.", permanent=True
            )
            emit.message(
                f"To use it, add {try_name!r} to the SDK list in a workshop and run {command!r}."
            )

    def remove(self, name: str, try_area: Path | None = None) -> None:
        """Atomically remove the named subdirectory of the try area."""
        if try_area is None:
            try_area = env.user_data_path() / "workshop" / "try"

        with (
            suppress(FileNotFoundError),
            TemporaryDirectory(prefix="tmp.", dir=try_area) as cleanup,
        ):
            (try_area / name).replace(cleanup)


def _copy_to(artifact: Path, target: Path, *, progress: bool) -> None:
    if progress:
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


def _rename(source: Path, target: Path) -> None:
    try:
        source.rename(target)
    except OSError as e:
        if e.errno != ENOTEMPTY:
            raise
    else:
        return

    # Poor approximation of `atomicswap.swap`.
    with TemporaryDirectory(dir=target.parent) as cleanup:
        target.replace(cleanup)
        source.rename(target)
