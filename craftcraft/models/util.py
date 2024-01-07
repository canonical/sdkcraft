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
"""Utility models for craftcraft."""
import enum

from craft_providers import bases

from craftcraft import const


class Architecture(enum.Enum):
    """Available architectures."""

    AMD64 = "amd64"
    ARM64 = "arm64"
    RISCV64 = "riscv64"
    PPC64EL = "ppc64el"
    S390X = "s390x"


class Base(enum.Enum):
    """Available bases, as strings."""

    # Mark supported and deprecated bases in const.py.
    FOCAL = "ubuntu@20.04"
    JAMMY = "ubuntu@22.04"
    MANTIC = "ubuntu@23.10"
    NOBLE = "ubuntu@24.04"

    def as_base_name(self) -> bases.BaseName:
        """Return the base as a craft-providers compatible BaseName."""
        name, version = self.value.split("@", maxsplit=1)
        return bases.BaseName(name, version)

    @property
    def is_supported(self) -> bool:
        """Check whether this base is supported."""
        return self.value in const.SUPPORTED_BASES

    @property
    def deprecated_version(self) -> str | None:
        """Get the version in which this base was deprecated, None if not deprecated."""
        return const.DEPRECATED_BASES.get(self.value, None)

    @property
    def is_experimental(self) -> bool:
        """Whether this base is experimental.

        Experimental bases may be removed in any release, even patch releases.
        """
        return self.deprecated_version is None and not self.is_supported
