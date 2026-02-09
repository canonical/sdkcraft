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
"""SDKcraft linting infrastructure."""

from __future__ import annotations

from enum import StrEnum, unique
from pathlib import Path

from craft_application.models import CraftBaseModel
from pydantic import HttpUrl

from sdkcraft.models.located import Location


@unique
class LinterResult(StrEnum):
    """Valid linting results."""

    ISSUE = "issue"
    WARNING = "warning"
    ERROR = "error"


class LinterIssue(CraftBaseModel):
    """Linter issue."""

    linter: str
    code: str | None = None
    result: LinterResult
    message: str
    url: HttpUrl | None = None

    path: Path
    abspath: Path | None = None
    location: Location = Location()
