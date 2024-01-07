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
import pytest_check
from craft_providers import bases
from craftcraft import const
from craftcraft.models import util


@pytest.mark.parametrize("base_name", const.SUPPORTED_BASES)
def test_supported_bases(base_name):
    """Tests for supported bases."""
    base = util.Base(base_name)
    pytest_check.is_true(base.is_supported, "Base should be supported but isn't")
    pytest_check.is_none(
        base.deprecated_version, "Supported base marked as deprecated."
    )
    pytest_check.is_false(
        base.is_experimental, "Supported base marked as experimental."
    )


@pytest.mark.parametrize(
    ("base_name", "deprecated_version"), const.DEPRECATED_BASES.items()
)
def test_deprecated_bases(base_name, deprecated_version):
    """Test outputs for deprecated bases."""
    base = util.Base(base_name)
    pytest_check.is_false(base.is_supported, "Deprecated base is marked supported.")
    pytest_check.is_false(
        base.is_experimental, "Deprecated base is marked experimental."
    )
    pytest_check.equal(base.deprecated_version, deprecated_version)


@pytest.mark.parametrize(
    ("base", "base_name"),
    [
        (util.Base.JAMMY, bases.BaseName("ubuntu", "22.04")),
        (util.Base.NOBLE, bases.BaseName("ubuntu", "24.04")),
    ],
)
def test_base_as_base_name(base, base_name):
    assert base.as_base_name() == base_name
