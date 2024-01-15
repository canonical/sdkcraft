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


import pytest
from sdkcraft import services


@pytest.fixture()
def extra_project_params():
    """Configuration fixture for the Project used by the default services."""
    return {}


@pytest.fixture()
def default_project(extra_project_params):
    from craft_application.models import ProjectName, VersionStr
    from sdkcraft.models.project import Project

    parts = extra_project_params.pop("parts", {})

    return Project(
        name=ProjectName("default"),
        version=VersionStr("1.0"),
        summary="default project",
        description="default project",
        base="ubuntu@22.04",
        parts=parts,
        license="MIT",
        platforms={"amd64": None},
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
        platform="amd64",
        build_for="amd64",
    )
