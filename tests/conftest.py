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
from pathlib import Path

import pytest
from sdkcraft import services


@pytest.fixture()
def extra_project_params():
    """Configuration fixture for the Project used by the default services."""
    return {"parts": {"default-part": {"plugin": "nil"}}}


@pytest.fixture()
def default_project(extra_project_params):
    from craft_application.models import Platform, ProjectName, SummaryStr, VersionStr
    from sdkcraft.models.project import Project

    parts = extra_project_params.pop("parts", {})
    plugs = {"content": {"target": "/path"}}

    return Project(
        name=ProjectName("default"),
        version=VersionStr("1.0"),
        summary=SummaryStr("default project"),
        description="default project",
        base="ubuntu@22.04",
        parts=parts,
        license="MIT",
        platforms={"amd64": Platform(build_on=["amd64"], build_for=["amd64"])},
        contact="requests@canonical.com",
        plugs=plugs,
        issues="https://github.com/canonical/sdk-store/issues",
        **extra_project_params,
    )


@pytest.fixture()
def default_factory(default_project):
    from sdkcraft.application import APP_METADATA
    from sdkcraft.services import ServiceFactory

    return ServiceFactory(
        app=APP_METADATA,
        LifecycleClass=services.Lifecycle,
        PackageClass=services.Package,
    )


@pytest.fixture()
def package_service(default_project, default_factory):
    from sdkcraft.application import APP_METADATA
    from sdkcraft.services import Package

    return Package(
        app=APP_METADATA,
        project=default_project,
        services=default_factory,
    )


@pytest.fixture()
def new_dir(tmpdir):
    """Change to a new temporary directory."""

    cwd = Path.cwd()
    os.chdir(tmpdir)

    yield tmpdir

    os.chdir(cwd)


@pytest.fixture()
def _reset_callbacks():
    """Fixture that resets the status of craft-part's various lifecycle callbacks,
    so that tests can start with a clean slate.
    """
    # pylint: disable=import-outside-toplevel

    from craft_parts import callbacks

    callbacks.unregister_all()
    yield
    callbacks.unregister_all()
