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
"""metadata.yaml description for SDKcraft output."""

from __future__ import annotations

import json
from pathlib import Path

from craft_application.models import (
    BaseMetadata,
    ProjectTitle,
    SummaryStr,
    UniqueStrList,
    VersionStr,
)
from pydantic import AnyUrl, ConfigDict

from sdkcraft.models.constraints import ProjectName
from sdkcraft.models.project import Plugs, Slots


class Metadata(BaseMetadata):
    """Structure to hold output metadata."""

    name: ProjectName
    title: ProjectTitle | None = None
    version: VersionStr | None = None
    summary: SummaryStr | None = None
    description: str | None = None

    base: str | None = None
    architecture: str

    contact: str | UniqueStrList | None = None
    issues: str | UniqueStrList | None = None
    source_code: AnyUrl | None = None
    license: str | None = None

    plugs: Plugs = {}
    slots: Slots = {}

    sdkcraft_started_at: str

    model_config = ConfigDict(use_enum_values=True)


def export_schema() -> None:
    """SDK metadata schema export.

    To run: uv run python sdkcraft/models/metadata.py.
    """
    schema = Metadata.model_json_schema()
    with Path("schema-sdk.json").open("w") as file:
        json.dump(schema, file, indent=2)


if __name__ == "__main__":
    # Call the export function
    export_schema()
