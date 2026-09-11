#  This file is part of sdkcraft.
#
# Copyright 2026 Canonical Ltd.
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
"""Tests for the runtime sdk.yaml metadata model."""

import pydantic
import pytest
from sdkcraft.models.metadata import Metadata

MINIMAL_METADATA = {
    "name": "my-sdk",
    "version": "1.0",
    "summary": "A summary",
    "description": "A description",
    "architecture": "amd64",
    "sdkcraft-started-at": "2026-01-01T00:00:00+00:00",
}


def test_metadata_schema_forbids_additional_properties():
    schema = Metadata.model_json_schema()

    assert schema["additionalProperties"] is False


def test_metadata_accepts_known_fields():
    metadata = Metadata.model_validate(
        MINIMAL_METADATA | {"website": "https://example.com"}
    )

    assert metadata.name == "my-sdk"
    assert str(metadata.website) == "https://example.com/"


def test_metadata_rejects_unknown_fields():
    with pytest.raises(pydantic.ValidationError, match="unknown-field"):
        Metadata.model_validate(MINIMAL_METADATA | {"unknown-field": "value"})
