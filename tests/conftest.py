# Copyright 2024 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranties of MERCHANTABILITY,
# SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

import os
import platform
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pytest
from craft_application.services import ServiceFactory
from craft_application.util import dump_yaml
from craft_parts.errors import PartsError
from craft_parts.utils.os_utils import OsRelease
from craft_platforms import DebianArchitecture
from sdkcraft.application import APP_METADATA
from sdkcraft.services import (
    BuildPlanService,
    PackageService,
    ProjectService,
    register_sdkcraft_services,
)

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def fake_arch_str() -> str:
    return "ppc64el"


@pytest.fixture
def fake_arch(
    fake_arch_str: str, monkeypatch: pytest.MonkeyPatch
) -> DebianArchitecture:
    arch = DebianArchitecture(fake_arch_str)
    real_uname = platform.uname
    monkeypatch.setattr(
        "platform.uname", lambda: real_uname()._replace(machine=arch.to_platform_arch())
    )
    return arch


@pytest.fixture
def project_data(fake_arch: DebianArchitecture) -> dict[str, Any]:
    return {
        "name": "default",
        "title": "default title",
        "version": "1.0",
        "summary": "default project",
        "description": "default project",
        "base": "ubuntu@22.04",
        "platforms": {str(fake_arch): None},
        "contact": "requests@canonical.com",
        "issues": "https://github.com/canonical/sdks/issues",
        "source-code": "https://github.com/canonical/sdks",
        "license": "MIT",
        "plugs": {"mount": {"interface": "mount", "workshop-target": "/path"}},
    }


@pytest.fixture
def default_factory(
    project_data: dict[str, Any], tmp_path_factory: pytest.TempPathFactory
) -> ServiceFactory:
    register_sdkcraft_services()
    factory = ServiceFactory(APP_METADATA)

    cache_dir = tmp_path_factory.mktemp("cache")
    project_dir = tmp_path_factory.mktemp("project")
    work_dir = tmp_path_factory.mktemp("work")

    with (project_dir / "sdkcraft.yaml").open("w") as f:
        dump_yaml(project_data, f)

    factory.update_kwargs("lifecycle", cache_dir=cache_dir, work_dir=work_dir)
    factory.update_kwargs("package", started_at=datetime.fromtimestamp(0, UTC))
    factory.update_kwargs("project", project_dir=project_dir)
    factory.update_kwargs("provider", work_dir=work_dir)

    return factory


@pytest.fixture
def package_service(default_factory: ServiceFactory) -> PackageService:
    return cast(PackageService, default_factory.get("package"))


@pytest.fixture
def project_service(default_factory: ServiceFactory) -> ProjectService:
    return cast(ProjectService, default_factory.get("project"))


@pytest.fixture
def package_service_with_configured_project(
    package_service: PackageService, project_service: ProjectService
) -> PackageService:
    project_service.configure(platform=None, build_for=None)
    return package_service


@pytest.fixture
def build_plan_service(default_factory: ServiceFactory) -> BuildPlanService:
    return cast(BuildPlanService, default_factory.get("build_plan"))


@pytest.fixture
def new_path(tmp_path: Path) -> Iterator[Path]:
    """Change to a new temporary directory."""

    cwd = Path.cwd()
    os.chdir(tmp_path)

    yield tmp_path

    os.chdir(cwd)


@pytest.fixture
def release_version() -> str:
    release = OsRelease()
    try:
        if release.id() == "ubuntu":
            return release.version_id()
        pytest.skip("platform must be Ubuntu")
    except (FileNotFoundError, PartsError) as e:
        # For non-Ubuntu platform, just skip this test case
        pytest.skip(f"failed to read Ubuntu release version: {e}")


@pytest.fixture
def state_dir(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fixture that makes StateService use a new directory for each test."""
    monkeypatch.setenv("CRAFT_STATE_DIR", str(tmp_path_factory.mktemp("state")))
