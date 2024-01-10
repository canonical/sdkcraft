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

from craft_application.models import BaseMetadata

from sdkcraft.models.util import Base


class Metadata(BaseMetadata):
    """Structure to hold output metadata."""

    name: str
    summary: str
    description: str
    version: str
    license: str
    base: Base

    class Config:
        """Metadata-specific Config for pydantic."""

        use_enum_values = True
