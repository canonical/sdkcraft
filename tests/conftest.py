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

import os
from datetime import datetime, timezone
from logging import warning
from pathlib import Path

import craft_parts.callbacks
import pytest
from sdkcraft.application import APP_METADATA
from sdkcraft.models.project import Project
from sdkcraft.services import ServiceFactory, register_sdkcraft_services


@pytest.fixture
def default_project_raw():
    return {
        "name": "default",
        "title": "default title",
        "version": "1.0",
        "summary": "default project",
        "description": "default project",
        "base": "ubuntu@22.04",
        "platforms": {"amd64": None},
        "contact": "requests@canonical.com",
        "issues": "https://github.com/canonical/sdks/issues",
        "source-code": "https://github.com/canonical/sdks",
        "license": "MIT",
        "plugs": {"mount": {"interface": "mount", "workshop-target": "/path"}},
    }


@pytest.fixture
def default_project(default_project_raw):
    return Project.unmarshal(default_project_raw)


@pytest.fixture
def default_factory(default_project, tmp_path_factory):
    register_sdkcraft_services()
    factory = ServiceFactory(APP_METADATA)

    cache_dir = tmp_path_factory.mktemp("cache")
    project_dir = tmp_path_factory.mktemp("project")
    work_dir = tmp_path_factory.mktemp("work")

    default_project.to_yaml_file(project_dir / "sdk.yaml")

    factory.update_kwargs("lifecycle", cache_dir=cache_dir, work_dir=work_dir)
    factory.update_kwargs("package", started_at=datetime.fromtimestamp(0, timezone.utc))
    factory.update_kwargs("project", project_dir=project_dir)
    factory.update_kwargs("provider", work_dir=work_dir)

    return factory


@pytest.fixture
def package_service(default_factory):
    return default_factory.get("package")


@pytest.fixture
def project_service(default_factory):
    return default_factory.get("project")


@pytest.fixture
def package_service_with_configured_project(package_service, project_service):
    project_service.configure(platform=None, build_for=None)
    return package_service


@pytest.fixture
def new_path(tmp_path):
    """Change to a new temporary directory."""

    cwd = Path.cwd()
    os.chdir(tmp_path)

    yield tmp_path

    os.chdir(cwd)


@pytest.fixture
def release_version():
    version = "22.04"
    try:
        with Path("/etc/os-release").open() as f:
            os_release = f.read()
        if "Ubuntu" in os_release:
            for line in os_release.splitlines():
                if line.startswith("VERSION_ID="):
                    version = line.split("=")[1].strip('"')
    except FileNotFoundError as e:
        # For non-Ubuntu platform, just skip this test case
        warning(f"failed to read Ubuntu release version, err={e}")
    return version


@pytest.fixture
def reset_callbacks():
    """Fixture that resets the status of craft-part's various lifecycle callbacks,
    so that tests can start with a clean slate.
    """
    craft_parts.callbacks.unregister_all()
    yield
    craft_parts.callbacks.unregister_all()
