#  This file is part of craftcraft.
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
"""Craftcraft project definition.

This module defines a craftcraft.yaml file, exportable to a JSON schema.
"""
from __future__ import annotations

import itertools
from typing import Any

import pydantic
from craft_application import models
from craft_application.models import (
    ProjectName,
    ProjectTitle,
    SummaryStr,
    UniqueStrList,
    VersionStr,
)
from craft_providers import bases
from pydantic import AnyUrl

from craftcraft.models import util
from craftcraft.models.util import Architecture


class Platform(models.CraftBaseModel):
    """A platform.

    Definition: https://docs.google.com/document/d/1HrGw_MpfJoMpoGRw74Qk3eP7cl7viwcmoPe9nICag2U/edit
    """

    build_on: Architecture | list[Architecture]
    build_for: Architecture | list[Architecture]

    @pydantic.validator("build_on", "build_for", pre=True)
    def vectorise(
        cls, value: str | Architecture | list[str | Architecture]
    ) -> list[Architecture]:
        """Make sure build on/for is a list of architectures."""
        if isinstance(value, str | Architecture):
            value = [value]
        return [Architecture(arch) for arch in value]


class Project(models.Project):
    """Craftcraft project definition."""

    name: ProjectName
    title: ProjectTitle | None
    version: VersionStr
    summary: SummaryStr
    description: str | None

    base: util.Base
    build_base: util.Base | None
    platforms: dict[str, Platform]

    contact: str | UniqueStrList | None
    issues: str | UniqueStrList | None
    source_code: AnyUrl | None
    license: str

    parts: dict[str, dict[str, Any]]  # parts are handled by craft-parts

    @pydantic.validator("platforms", pre=True)
    def pre_parse_platforms(
        cls, platforms: dict[str, Any]
    ) -> dict[str, dict[list[str], list[str]]]:
        """Pre-parse platforms section.

        This ensures that each platform has both a build_on and build_for.
        """
        for name, value in platforms.items():
            if value is None:
                platforms[name] = {
                    "build-on": [Architecture(name)],
                    "build-for": [Architecture(name)],
                }
            elif isinstance(value, dict) and "build-for" not in value:
                value["build-for"] = [Architecture(name)]

        return platforms

    @property
    def effective_base(self) -> bases.BaseName:
        """Base name for craft-providers."""
        build_base = getattr(self, "build_base", None)
        if isinstance(build_base, util.Base):
            return build_base.as_base_name()
        return self.base.as_base_name()

    def get_build_plan(self) -> list[models.BuildInfo]:
        """Obtain the list of architectures and bases from the project file."""
        base = self.effective_base

        build_infos: list[models.BuildInfo] = []

        for platform_name, platform in self.platforms.items():
            build_ons = platform.build_on
            build_fors = platform.build_for
            if not isinstance(build_ons, list):
                build_ons = [build_ons]
            if not isinstance(build_fors, list):
                build_fors = [build_fors]

            for build_on, build_for in itertools.product(build_ons, build_fors):
                build_infos.append(
                    models.BuildInfo(
                        platform=platform_name,
                        build_on=build_on.value,
                        build_for=build_for.value,
                        base=base,
                    )
                )

        return build_infos
