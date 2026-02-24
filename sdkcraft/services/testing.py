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
"""SDKcraft testing service."""

from __future__ import annotations

import re
import shlex
import shutil
import subprocess
from os import EX_CONFIG, EX_NOINPUT
from os.path import normpath
from pathlib import Path
from signal import SIGINT
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, cast, override

from craft_application import services
from craft_application.errors import CraftValidationError
from craft_application.models import CraftBaseModel
from craft_application.util import dump_yaml, safe_yaml_load
from craft_cli import CraftError, emit
from craft_platforms import DistroBase
from craft_providers.bases import BaseName, BuilddBaseAlias, get_base_alias
from pydantic import ConfigDict, ValidationError

from sdkcraft.errors import SpreadFileMissingError, SpreadListError
from sdkcraft.services.tryservice import TryService

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping


SPREAD_PREPARE = """\
# Install Workshop and try out packed SDKs.
sudo snap wait system seed.loaded

if snap list lxd >/dev/null; then
    sudo snap refresh --channel=6/stable lxd
else
    sudo snap install --channel=6/stable lxd
fi
lxd waitready --timeout=180

sudo snap install --classic --dangerous ./workshop_*.snap

rm -rf ~/.local/share/workshop/try
install --directory --mode=700 ~/.local
install --directory --mode=755 ~/.local/share/workshop/try
ln --symbolic "$(pwd)"/TEMPNAME/try/* ~/.local/share/workshop/try/
"""
SPREAD_PREPARE_SEP = """\

# Run original prepare script.
"""

# Job names look like backend:system:task(:variant)?(#sample)?.
SPREAD_VARIANT_INDEX = 3
SPREAD_SAMPLE = re.compile(r"#\d+$")

# Wait 5 minutes after SIGINT because spread tasks can't be interrupted.
SIGINT_TIMEOUT = 5 * 60.0


class SpreadProject(CraftBaseModel):
    """A spread project with only the attributes we need."""

    reroot: str = ""
    prepare: str = ""

    model_config = ConfigDict(extra="allow", populate_by_name=False)


class TestingService(services.TestingService):
    """Testing service for SDKcraft."""

    def sanity_check(self, project_path: Path) -> None:
        """Detect errors without waiting for long operations."""
        _, _, spread_path = _read_spread_yaml(project_path)
        if next(spread_path.glob("workshop_*.snap"), None) is None:
            raise CraftError(
                f"Workshop snap not found in {str(spread_path)!r}.",
                details="A local copy of the snap is required while Workshop remains private.",
                reportable=False,
                logpath_report=False,
                retcode=EX_NOINPUT,
            )

    def sdkcraft_test(
        self,
        project_path: Path,
        artifacts: Mapping[str, Path],
        *,
        test_expressions: Iterable[str] = (),
        bases: Iterable[str | None] = (),
        shell: bool = False,
        shell_after: bool = False,
        debug: bool = False,
    ) -> None:
        """Run SDK tests."""
        emit.progress("Running tests...")

        _, spread, spread_path = _read_spread_yaml(project_path)
        with TemporaryDirectory(
            prefix=".craft-spread-",
            dir=spread_path,
        ) as temp_dir:
            temp_path = Path(temp_dir)
            emit.trace(f"Temporary spread directory: {temp_path}")

            processed = _process_spread_project(spread, temp_path)
            _write_spread_yaml(processed, temp_path)

            try_area = temp_path / "try"
            try_area.mkdir()
            try_service = cast(TryService, self._services.get("try"))
            try_service.copy(self._project.name, artifacts, try_area)

            jobs = self._filter_spread_jobs_by_base(
                temp_path,
                test_expressions=test_expressions,
                bases=bases,
            )
            if not jobs:
                emit.progress("No tests to run.", permanent=True)
                return

            self.run_spread(
                temp_path,
                test_expressions=jobs,
                shell=shell,
                shell_after=shell_after,
                debug=debug,
            )

        emit.progress("Testing successful.", permanent=True)

    def list_tests(
        self,
        project_path: Path,
        *,
        test_expressions: Iterable[str] = (),
        bases: Iterable[str | None] = (),
    ) -> None:
        """List SDK tests."""
        path, _, _ = _read_spread_yaml(project_path)

        jobs = self._filter_spread_jobs_by_base(
            path.parent,
            test_expressions=test_expressions,
            bases=bases,
        )

        for job in jobs:
            emit.message(job)

    def _filter_spread_jobs_by_base(
        self,
        spread_path: Path,
        *,
        test_expressions: Iterable[str],
        bases: Iterable[str | None],
    ) -> list[str]:
        spread_command = self._get_spread_list_command(test_expressions)
        try:
            proc = subprocess.run(
                spread_command,
                capture_output=True,
                text=True,
                check=True,
                cwd=spread_path,
            )
        except subprocess.CalledProcessError as e:
            raise SpreadListError(e)

        jobs = proc.stdout.splitlines()
        distro_bases: list[DistroBase] = []
        for base in bases:
            if base is None:
                # The SDK is base-agnostic and all variants should work.
                break
            distro_bases.append(DistroBase.from_str(base))
        else:
            jobs = list(filter(JobFilter(distro_bases), jobs))

        emit.debug(f"filtered jobs: {jobs}")
        return jobs

    @override
    def _get_spread_command(
        self,
        *,
        test_expressions: Iterable[str] = (),
        shell: bool = False,
        shell_after: bool = False,
        debug: bool = False,
        cwd: Path | None = None,
    ) -> list[str]:
        cmd = [self._get_spread_executable(), "-reuse", "-resend"]
        if shell:
            cmd.append("-shell")
        if shell_after:
            cmd.append("-shell-after")
        if debug:
            cmd.append("-debug")
        cmd.extend(test_expressions)

        emit.debug(f"Running spread as: {shlex.join(cmd)}")
        return cmd

    @override
    def run_spread(
        self,
        spread_dir: Path,
        *,
        test_expressions: Iterable[str] = (),
        shell: bool = False,
        shell_after: bool = False,
        debug: bool = False,
    ) -> None:
        emit.debug("Running spread tests.")
        spread_command = self._get_spread_command(
            test_expressions=test_expressions,
            shell=shell,
            shell_after=shell_after,
            debug=debug,
            cwd=spread_dir,
        )

        try:
            with emit.pause():
                _run_spread(spread_command, spread_dir)
        except subprocess.CalledProcessError as exc:
            raise CraftError(
                "Testing failed.",
                reportable=False,
                retcode=exc.returncode,
            )

    def clean(self, project_path: Path) -> None:
        """Discard leftover spread environment(s)."""
        try:
            path, _, spread_path = _read_spread_yaml(project_path)
        except CraftError:
            return

        cmd = [self._get_spread_executable(), "-discard"]
        with emit.open_stream("Discarding spread environments") as stream:
            subprocess.run(
                cmd,
                check=True,
                stdout=stream,
                stderr=stream,
                cwd=path.parent,
            )

        for path in spread_path.glob(".craft-spread-*"):
            emit.trace(f"Removing {path}")
            shutil.rmtree(path, ignore_errors=True)


def _read_spread_yaml(project_path: Path) -> tuple[Path, SpreadProject, Path]:
    emit.debug("Processing spread.yaml.")

    path = project_path / "tests" / "spread.yaml"
    try:
        with path.open() as f:
            data = safe_yaml_load(f)
    except FileNotFoundError:
        raise SpreadFileMissingError(
            f"Project file {path.name!r} not found in {str(path.parent)!r}.",
            resolution="Run 'sdkcraft init' to generate a sample test suite.",
            reportable=False,
            logpath_report=False,
            retcode=EX_NOINPUT,
        )

    try:
        spread = SpreadProject.unmarshal(data)
    except ValidationError as e:
        raise CraftValidationError.from_pydantic(
            e, file_name=path.name, logpath_report=False
        )

    spread_path = path.parent
    if spread.reroot:
        spread_path = Path(normpath(spread_path / spread.reroot))
        # In principle we could allow arbitrary reroots, but we should
        # avoid spraying .craft-spread directories all over the system.
        if not spread_path.is_relative_to(project_path):
            raise CraftError(
                f"Spread directory {spread_path!r} is outside the project.",
                resolution=f"Update reroot in {path.name!r}.",
                reportable=False,
                logpath_report=False,
                retcode=EX_CONFIG,
            )

    return path, spread, spread_path


def _process_spread_project(project: SpreadProject, temp_path: Path) -> SpreadProject:
    prepare = SPREAD_PREPARE.replace("TEMPNAME", temp_path.name)
    if project.prepare:
        prepare += SPREAD_PREPARE_SEP
        prepare += project.prepare

    return project.model_copy(update={"reroot": "..", "prepare": prepare})


def _write_spread_yaml(project: SpreadProject, temp_path: Path) -> None:
    data = project.model_dump(
        mode="json", by_alias=True, exclude_unset=True, round_trip=True
    )

    target = temp_path / "spread.yaml"
    emit.trace(f"Writing processed spread file to {target}")
    with target.open("w") as f:
        dump_yaml(data, f)
    emit.trace(f"Temporary spread file:\n{target.read_text()}")


class JobFilter:
    """Filter spread jobs by base."""

    def __init__(self, bases: Iterable[DistroBase]) -> None:
        aliases = {
            get_base_alias(BaseName(name=base.distribution, version=base.series))
            for base in bases
        }
        self.variants = {
            alias.name.lower(): alias in aliases for alias in BuilddBaseAlias
        }

    def __call__(self, job: str) -> bool:
        """Determine whether the given job should be included."""
        variant = _job_variant(job)
        if variant is None:
            return True
        return self.variants.get(variant.lower(), True)


def _job_variant(job: str) -> str | None:
    parts = job.split(":", SPREAD_VARIANT_INDEX)
    if len(parts) <= SPREAD_VARIANT_INDEX:
        return None

    variant = parts[SPREAD_VARIANT_INDEX]
    if m := SPREAD_SAMPLE.search(variant):
        variant = variant[: m.start()]

    return variant


def _run_spread(command: list[str], cwd: Path) -> None:
    # Like subprocess.run but waits longer after KeyboardInterrupt.
    with subprocess.Popen(command, cwd=cwd) as process:
        try:
            process.wait()
        except KeyboardInterrupt:
            try:
                process.send_signal(SIGINT)
                process.wait(SIGINT_TIMEOUT)
            except subprocess.TimeoutExpired:
                # Raise original exception for nicer output.
                pass
            finally:
                process.kill()
            raise
        except:
            process.kill()
            raise

        retcode = process.poll()
        if retcode:
            raise subprocess.CalledProcessError(retcode, process.args)
