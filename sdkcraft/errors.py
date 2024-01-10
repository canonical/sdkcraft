# Copyright 2024 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Sdkcraft error definitions."""

from craft_cli import CraftError
from craft_parts import PartsError


class SdkcraftError(CraftError):
    """Failure in a Sdkcraft operation."""


class SdkcraftInitError(SdkcraftError):
    """Error while initializing sdkcraft project."""

    def __init__(self, yaml_path: str) -> None:
        super().__init__(f"{yaml_path} already exists!")


class PartsLifecycleError(SdkcraftError):
    """Error during parts processing."""

    @staticmethod
    def from_parts_error(err: PartsError) -> "PartsLifecycleError":
        """Shortcut to create a PartsLifecycleError from a PartsError."""
        return PartsLifecycleError(
            message=err.brief, details=err.details, resolution=err.resolution
        )


class ProjectLoadError(SdkcraftError):
    """Error loading sdkcraft.yaml."""
