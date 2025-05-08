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

import pytest
from pydantic import AnyUrl
from sdkcraft import services


@pytest.fixture
def default_project():
    from craft_application.models import Platform
    from sdkcraft.models.project import MountPlug, Plug, Project

    plugs: dict[str, Plug] = {
        "mount": MountPlug(interface="mount", workshop_target="/path")
    }

    return Project(
        name="default",
        title="default title",
        version="1.0",
        summary="default project",
        description="default project",
        source_code=AnyUrl("https://github.com/canonical/sdks/"),
        base="ubuntu@22.04",
        license="MIT",
        platforms={"amd64": Platform(build_on=["amd64"], build_for=["amd64"])},
        contact="requests@canonical.com",
        plugs=plugs,
        issues="https://github.com/canonical/sdks/issues",
    )


@pytest.fixture
def default_factory(default_project, tmp_path_factory):
    from sdkcraft.application import APP_METADATA
    from sdkcraft.services import ServiceFactory

    ServiceFactory.register("lifecycle", services.Lifecycle)
    ServiceFactory.register("package", services.Package)

    factory = ServiceFactory(app=APP_METADATA, project=default_project)

    factory.update_kwargs(
        "lifecycle",
        cache_dir=tmp_path_factory.mktemp("cache"),
        work_dir=tmp_path_factory.mktemp("work"),
        build_plan=[],
    )

    factory.update_kwargs("package", started_at=datetime.fromtimestamp(0, timezone.utc))

    return factory


@pytest.fixture
def package_service(default_factory):
    return default_factory.package


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
def _reset_callbacks():
    """Fixture that resets the status of craft-part's various lifecycle callbacks,
    so that tests can start with a clean slate.
    """
    # pylint: disable=import-outside-toplevel

    from craft_parts import callbacks

    callbacks.unregister_all()
    yield
    callbacks.unregister_all()
