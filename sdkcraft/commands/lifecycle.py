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

import os
import textwrap
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast, override

from craft_application.commands import lifecycle
from craft_application.errors import CraftValidationError
from craft_application.util import is_managed_mode
from craft_cli import CraftError
from craft_platforms import DebianArchitecture
from pydantic import TypeAdapter, ValidationError

from sdkcraft.errors import SdkcraftFilenameError
from sdkcraft.models.constraints import ProjectName
from sdkcraft.services import TestingService, TryService

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace
    from collections.abc import Iterable, Iterator, Mapping

    from craft_application import PackageService
    from craft_platforms import BuildInfo


class PackCommand(lifecycle.PackCommand):
    """Command to pack the final artifact."""

    hidden = False
    examples: list[tuple[str, str]] = [
        ("Pack the project", "sdkcraft pack"),
        ("Pack to a specific output directory", "sdkcraft pack --output dist/"),
    ]
    related_commands: list[str] | None = None

    _show_lxd_arg = False

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


class TestCommand(PackCommand):
    """Run SDK tests using spread."""

    name = "test"
    help_msg = "Run SDK tests"
    overview = textwrap.dedent(
        """
        Tests are defined and run using spread (https://github.com/canonical/spread).

        Compared to running spread manually, `sdkcraft test` also:
        - Packs SDKs for all platforms matching the current architecture.
        - Copies the packed SDKs into the test environment using `sdkcraft try`.
        - Installs Workshop in the test environment.
        - Skips spread variants for bases that weren't packed.
        """
    )
    common = True
    _allow_build_for = False

    @override
    def _fill_parser(self, parser: ArgumentParser) -> None:
        # Skip the parser additions that `pack` adds.
        super(lifecycle.PackCommand, self)._fill_parser(parser)
        parser.add_argument(
            "test_expressions",
            nargs="*",
            type=str,
            default=(),
            help="Optional spread test expressions. If not provided, all tests are run.",
        )

    @override
    def _run(
        self,
        parsed_args: Namespace,
        step_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        dirs = self._services.get("lifecycle").project_info.dirs
        parsed_args.output = dirs.project_dir

        testing_service = cast(TestingService, self._services.get("testing"))
        testing_service.sanity_check(dirs.project_dir)

        # Don't enter a shell during the packing step, but save those values
        # for the testing service.
        shell, shell_after = parsed_args.shell, parsed_args.shell_after
        parsed_args.shell, parsed_args.shell_after = (False, False)

        if not is_managed_mode():
            build_for = DebianArchitecture.from_host()
            self.services.get("build_plan").set_build_fors(build_for)

        super()._run(parsed_args, step_name, **kwargs)
        if is_managed_mode():
            # If we're in managed mode, we just need to pack.
            return

        build_plan = self._services.get("build_plan").plan()
        package = self._services.get("package")
        artifacts = {
            build_info.platform: _artifact(package, build_info)
            for build_info in build_plan
        }

        testing_service.sdkcraft_test(
            dirs.project_dir,
            artifacts,
            test_expressions=parsed_args.test_expressions,
            shell=shell,
            shell_after=shell_after,
            debug=parsed_args.debug,
        )


class TryCommand(PackCommand):
    """Try out an SDKcraft project."""

    name = "try"
    help_msg = "Try SDKs before publishing"
    overview = textwrap.dedent(
        """
        Pack the SDK and copy it to the Workshop try area.
        """
    )
    hidden = False
    examples: list[tuple[str, str]] = [
        ("Try the built artifact", "sdkcraft try"),
    ]
    related_commands: list[str] | None = None

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

        try_service = cast(TryService, self._services.get("try"))
        try_service.copy(name, artifacts, progress=True)


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


class CleanCommand(lifecycle.CleanCommand):
    """Command to remove part assets."""

    hidden = False
    examples: list[tuple[str, str]] = [
        ("Clean build artifacts", "sdkcraft clean"),
        ("Clean specific parts", "sdkcraft clean my-part"),
        ("Clean in destructive mode", "sdkcraft clean --destructive-mode"),
    ]
    related_commands: list[str] | None = None

    _show_lxd_arg = False

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
            dirs = self._services.get("lifecycle").project_info.dirs
            testing_service = cast(TestingService, self._services.get("testing"))
            testing_service.clean(dirs.project_dir)

            try_service = cast(TryService, self._services.get("try"))
            try_service.remove(self._project.name)
