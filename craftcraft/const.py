# This file is part of craftcraft.
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
"""Global constants to use in craftcraft."""

# Bases supported by this application.
SUPPORTED_BASES = [
    "ubuntu@22.04",
]

# Bases that , as well as the version in which they were deprecated.
DEPRECATED_BASES: dict[str, str] = {
    # Map the base name to the version in which it was deprecated.
    "ubuntu@20.04": "0.0",
}
