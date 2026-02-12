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
"""Linter for interfaces."""

from __future__ import annotations

from pathlib import Path
from string import Template

from sdkcraft.dirs import WORKSHOP_SDKS_DIR
from sdkcraft.models import LinterIssue, LinterResult, MarkedProject


class InterfaceCheck:
    """InterfaceCheck linter for SDK plugs and slots."""

    def run(self, prime_dir: Path, project: MarkedProject) -> list[LinterIssue]:
        """Validate plugs and slots."""
        sdk_dir = WORKSHOP_SDKS_DIR / project.name

        issues: list[LinterIssue] = []
        template = LinterIssue(
            linter="mount-interface",
            result=LinterResult.ERROR,
            message="path not found",
            path=project.path,
            abspath=project.abspath,
        )

        for name, plug in project.plugs.items():
            if plug.interface != "mount":
                continue

            missing = _missing_path(prime_dir, plug.workshop_target.value, sdk_dir)
            if missing is None:
                continue

            update = {
                "message": f"workshop-target {missing!r} not found for {name!r} mount plug",
                "location": plug.workshop_target.location,
            }
            issues.append(template.model_copy(update=update))

        for name, slot in project.slots.items():
            if slot.interface != "mount":
                continue

            missing = _missing_path(prime_dir, slot.workshop_source.value, sdk_dir)
            if missing is None:
                continue

            update = {
                "message": f"workshop-source {missing!r} not found for {name!r} mount slot",
                "location": slot.workshop_source.location,
            }
            issues.append(template.model_copy(update=update))

        return issues


def _missing_path(prime_dir: Path, path: str, sdk_dir: Path) -> str | None:
    expanded = Template(path).substitute(SDK=sdk_dir)
    try:
        relative = Path(expanded).relative_to(sdk_dir)
    except ValueError:
        return None

    if (prime_dir / relative).exists():
        return None

    return f"$SDK/{relative}"
