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
"""Tests for utility models."""

import pytest
from sdkcraft import models
from sdkcraft.models.util import Base


@pytest.mark.parametrize(
    ("meta_data", "expected"),
    [(
        models.Metadata(
            name="sdk",
            summary="Default SDK summary string",
            description="SDK description",
            version="0.1",
            license="GPL-3.0",
            base=Base.JAMMY,
        ),
        {"name": "sdk",
         "description":"SDK description",
         "version":"0.1",
         "license":"GPL-3.0",
         "summary": "Default SDK summary string",
         "base":"ubuntu@22.04"}
    )]
)
def test_metadata(meta_data, expected):
    assert meta_data.marshal() == expected
