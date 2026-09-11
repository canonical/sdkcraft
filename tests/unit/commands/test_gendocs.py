# Copyright 2026 Canonical Ltd.
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

"""Tests for the hidden generate-docs command and its templates."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from gencodo import CommandGroup, gen_docs_tree, validate_templates
from sdkcraft.cli import _create_app
from sdkcraft.commands.gendocs import FILE_PREFIX, INDEX_FILE_NAME, load_templates

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any


def test_templates_render() -> None:
    """A template referencing an unknown variable must fail here, not in CI docs jobs."""
    validate_templates(load_templates(), appname="sdkcraft")


@pytest.fixture
def command_groups() -> list[CommandGroup]:
    return [
        CommandGroup(name=group.name, commands=group.commands)
        for group in _create_app().command_groups
    ]


def test_generate_reference(
    tmp_path: Path, app_config: dict[str, Any], command_groups: list[CommandGroup]
) -> None:
    generated = gen_docs_tree(
        appname="sdkcraft",
        command_groups=command_groups,
        output_dir=tmp_path,
        templates=load_templates(),
        file_extension=".rst",
        command_config=app_config,
        file_prefix=FILE_PREFIX,
    )

    assert all(name.startswith(FILE_PREFIX) for name in generated)
    assert "sdkcraft-generate-docs.rst" not in generated, "hidden commands are skipped"
    assert (tmp_path / INDEX_FILE_NAME).is_file()

    pack = (tmp_path / "sdkcraft-pack.rst").read_text()
    assert ".. _ref_sdkcraft_pack:" in pack
    assert "-o, --output" in pack, "short options are documented"
    assert "Default: :samp:`False`" not in pack, "value-less flags show no default"

    release = (tmp_path / "sdkcraft-release.rst").read_text()
    assert ".. rubric:: Arguments" in release
    assert "SDK\n" in release, "positional arguments are documented"

    index = (tmp_path / INDEX_FILE_NAME).read_text()
    assert ".. include:: sdkcraft-pack.rst" in index
