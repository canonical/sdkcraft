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

from __future__ import annotations

import errno
import json
import os
import shutil
import subprocess
import textwrap
from contextlib import ExitStack, suppress
from hashlib import file_digest, sha3_384
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any

from craft_application.commands import lifecycle
from craft_application.errors import CraftValidationError
from craft_application.util import is_managed_mode
from craft_cli import CraftError, emit
from pydantic import TypeAdapter, ValidationError
from typing_extensions import override

from sdkcraft.env import user_data_path
from sdkcraft.errors import SdkcraftFilenameError
from sdkcraft.models.constraints import ProjectName

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace
    from collections.abc import Iterable, Iterator, Mapping

    from craft_application import PackageService
    from craft_platforms import BuildInfo


class PackCommand(lifecycle.PackCommand):
    """Command to pack the final artifact."""

    @override
    def _run_post_prime_steps(self) -> None:
        super()._run_post_prime_steps()
        self._lint_hooks()

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

    def _lint_hooks(self) -> None:
        """Run shellcheck linting on hooks directory."""
        dirs = self._services.get("lifecycle").project_info.dirs
        hooks_dir = dirs.project_dir / "hooks"
        ignore_severities = self._project.lint.ignore.shellcheck
        _run_shellcheck_on_hooks(hooks_dir, ignore_severities)


def _run_shellcheck_on_hooks(hooks_dir: Path, ignore_severities: list[str]) -> None:
    """Run shellcheck on all scripts in hooks directory."""
    if not hooks_dir.is_dir():
        return

    script_files = [
        entry
        for entry in hooks_dir.iterdir()
        if entry.is_file() and not entry.is_symlink()
    ]

    if not script_files:
        return

    emit.progress("Linting hooks with shellcheck...")

    has_errors = False
    warnings: list[str] = []

    for script in script_files:
        result = subprocess.run(
            ["shellcheck", "--format=json", str(script)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            continue

        try:
            issues = json.loads(result.stdout)
        except json.JSONDecodeError:
            emit.message(
                f"Warning: Could not parse shellcheck output for {script.name}"
            )
            continue

        for issue in issues:
            severity = str(issue.get("level", "")).lower()
            if severity in ignore_severities:
                continue

            line = issue.get("line", "?")
            col = issue.get("column", "?")
            code = str(issue.get("code", ""))
            message = issue.get("message", "")
            issue_msg = f"{script.name}:{line}:{col}: [{severity}] {message} (SC{code})"

            if severity == "error" and code != "2148":
                emit.message(issue_msg)
                has_errors = True
            else:
                warnings.append(issue_msg)

    if warnings:
        emit.progress("Shellcheck warnings:", permanent=True)
        for warning in warnings:
            emit.message(warning)

    if has_errors:
        raise CraftError(
            "Shellcheck found errors in hooks scripts.",
            resolution=(
                "Fix the errors reported above or add them to "
                "'lint.ignore.shellcheck' in sdkcraft.yaml"
            ),
        )

    emit.progress("Linting completed successfully.", permanent=True)


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
    def _fill_parser(self, parser: ArgumentParser) -> None:
        super()._fill_parser(parser)

        parser.add_argument(
            "sdks",
            metavar="SDKs",
            type=Path,
            nargs="*",
            help="Skip packing and try out specific SDK files.",
        )
        parser.format_usage()

    @override
    def needs_project(self, parsed_args: Namespace) -> bool:
        return not parsed_args.sdks

    @override
    def _run(
        self, parsed_args: Namespace, step_name: str | None = None, **kwargs: Any
    ) -> None:
        if parsed_args.sdks:
            for name, artifacts in _sdks_by_name(parsed_args.sdks).items():
                self._try(name, artifacts)
            return

        super()._run(parsed_args=parsed_args, step_name=step_name, **kwargs)
        if is_managed_mode():
            # If we're in managed mode, we just need to pack.
            return

        build_plan = self._services.get("build_plan").plan()
        package = self._services.get("package")
        artifacts = {
            build_info.platform: _artifact(package, build_info)
            for build_info in build_plan
        }

        self._try(self._project.name, artifacts)

    def _try(self, name: str, artifacts: Mapping[str, Path]) -> None:
        if not artifacts:
            return

        try_area = user_data_path() / "workshop" / "try"
        try_area.mkdir(parents=True, exist_ok=True)

        with ExitStack() as stack:
            target = Path(stack.enter_context(TemporaryDirectory(dir=try_area)))

            for artifact in artifacts.values():
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

        platforms = ", ".join(artifacts.keys())
        try_name = f"try-{name}"
        command = "workshop refresh"

        emit.progress(
            f"Copied {name} SDK ({platforms}) to the try area.", permanent=True
        )
        emit.message(
            f"To use it, add {try_name!r} to the SDK list in a workshop and run {command!r}."
        )


def _sdks_by_name(sdks: Iterable[Path]) -> dict[str, dict[str, Path]]:
    by_name: dict[str, dict[str, Path]] = {}

    for sdk in sdks:
        parts = sdk.stem.split("_", 2)
        if len(parts) <= 1:
            raise SdkcraftFilenameError(sdk.name)

        name, *rest = parts
        try:
            TypeAdapter(ProjectName).validate_python(name)
        except ValidationError as e:
            raise CraftValidationError.from_pydantic(e, file_name="filename") from None

        if len(rest) == 1:
            (platform,) = rest
        else:
            arch, base = rest
            platform = f"{base}:{arch}"

        by_name.setdefault(name, {})[platform] = sdk

    return by_name


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


class CleanCommand(lifecycle.CleanCommand):
    """Command to remove part assets."""

    @override
    def _run(
        self,
        parsed_args: Namespace,
        **kwargs: Any,
    ) -> None:
        """Run the clean command.

        The project's work directory will be cleaned if:
        - the `--destructive-mode` flag is provided OR
        - `CRAFT_BUILD_ENVIRONMENT` is set to `host` OR
        - no list of specific parts to clean is provided

        Otherwise, it will clean an instance.
        """
        super()._run(parsed_args, **kwargs)

        if not parsed_args.parts:
            _remove_try_sdk(self._project.name)


def _remove_try_sdk(name: str) -> None:
    try_area = user_data_path() / "workshop" / "try"
    with (
        suppress(FileNotFoundError),
        TemporaryDirectory(dir=try_area) as cleanup,
    ):
        (try_area / name).replace(cleanup)
