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
"""metadata.yaml description for sdkcraft output."""

from typing import Any

from craft_application.models import (
    BaseMetadata,
    ProjectTitle,
    SummaryStr,
    UniqueStrList,
)
from pydantic import AnyUrl

from sdkcraft.models.project import MountPlug


class Metadata(BaseMetadata):
    """Structure to hold output metadata."""

    name: str
    title: ProjectTitle | None
    base: Any
    version: str | None
    summary: SummaryStr
    license: str
    description: str
    contact: str | UniqueStrList | None
    issues: str | UniqueStrList | None
    source_code: AnyUrl | None
    sdkcraft_started_at: str
    plugs: dict[str, MountPlug | Any] | None

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # Setting attributes of Config
        self.model_config["use_enum_values"] = True
