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
"""SDKcraft build planning service."""

from __future__ import annotations

from itertools import chain, product
from typing import TYPE_CHECKING, Any, override

from craft_application.services import buildplan
from craft_platforms import (
    AllOnlyBuildError,
    BuildInfo,
    DistroBase,
    InvalidMultiBaseError,
    RequiresBaseError,
    parse_base_and_architecture,
)

from sdkcraft.errors import RepeatedPlatformError
from sdkcraft.models.project import Project

if TYPE_CHECKING:
    from collections.abc import Iterable


class BuildPlanService(buildplan.BuildPlanService):
    """A service for generating and filtering build plans."""

    @override
    def _gen_exhaustive_build_plan(
        self, project_data: dict[str, Any]
    ) -> Iterable[BuildInfo]:
        """Generate the exhaustive build plan with craft-platforms.

        :param project_data: The unprocessed project data retrieved from a YAML file.
        :returns: An iterable of BuildInfo objects that make the exhaustive build plan.
        """

        _ = project_data  # Ignored because the bases have been stripped.
        project = Project.unmarshal(self._services.get("project").get_raw())

        build_plan: list[BuildInfo] = []
        platform_names: dict[tuple[str | None, str], list[str]] = {}

        for platform_name, platform in project.platforms.items():
            build_on = _vectorize(platform.build_on)
            build_for = _vectorize(platform.build_for)

            base, build_base = _get_base_from_build_data(
                project.base, project.build_base, platform_name, build_on, build_for
            )

            for b in build_for:
                _, arch = parse_base_and_architecture(b)
                platform_names.setdefault((base, arch), []).append(platform_name)

            build_plan.extend(
                _build_info(platform_name, build_base, on, fr)
                for on, fr in product(build_on, build_for)
            )

        for names in platform_names.values():
            if len(names) > 1:
                raise RepeatedPlatformError(names)

        build_fors = {info.build_for for info in build_plan}
        if len(build_fors) > 1 and "all" in build_fors:
            agnostic = {info.platform for info in build_plan if info.build_for == "all"}
            raise AllOnlyBuildError(agnostic)

        return build_plan


def _vectorize(items: list[str] | str) -> list[str]:
    if isinstance(items, str):
        return [items]
    return items


def _get_base_from_build_data(
    base: str | None,
    build_base: str | None,
    platform_name: str,
    build_on: list[str],
    build_for: list[str],
) -> tuple[str | None, DistroBase]:
    bases = {_parse_base(platform) for platform in chain(build_on, build_for)}
    if len(bases) != 1:
        raise InvalidMultiBaseError(
            message=(
                f"Platform {platform_name!r} has mismatched bases in the 'build-on' "
                "and 'build-for' entries."
            ),
            resolution=(
                "Use the same base for all 'build-on' and 'build-for' entries for "
                "the platform."
            ),
        )

    (platform_base,) = bases
    if platform_base and (base or build_base):
        raise InvalidMultiBaseError(
            message=f"Platform {platform_name!r} declares a base and a top-level base "
            "or build-base is declared.",
            resolution=(
                "Remove the base from the platform's name or remove the top-level base "
                "or build-base."
            ),
        )

    final_base = base or (None if build_base else platform_base)
    final_build_base = build_base or base or platform_base
    if not final_build_base:
        raise RequiresBaseError(
            message=(
                "No base or build-base is declared and no base is declared "
                "in the platforms section."
            ),
            resolution="Declare a base or build-base.",
        )

    return final_base, DistroBase.from_str(final_build_base)


def _parse_base(platform: str) -> str | None:
    distro_base, _ = parse_base_and_architecture(platform)
    return None if distro_base is None else str(distro_base)


def _build_info(
    platform_name: str, distro_base: DistroBase, build_on: str, build_for: str
) -> BuildInfo:
    _, build_on_arch = parse_base_and_architecture(build_on)
    if build_on_arch == "all":
        raise ValueError(
            f"Platform {platform_name!r} has an invalid 'build-on' entry of 'all'."
        )

    _, build_for_arch = parse_base_and_architecture(build_for)

    return BuildInfo(
        platform=platform_name,
        build_on=build_on_arch,
        build_for=build_for_arch,
        build_base=distro_base,
    )
