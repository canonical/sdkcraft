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

"""SDKcraft error definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from craft_cli import CraftError
from craft_platforms import CraftPlatformsError

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


class SdkcraftError(CraftError):
    """Failure in a SDKcraft operation."""


class SdkcraftInitError(SdkcraftError):
    """Error while initializing SDKcraft project."""

    def __init__(self, yaml_path: Path) -> None:
        super().__init__(f"{yaml_path} already exists!")


class SdkcraftFilenameError(SdkcraftError):
    """Error when parsing a packed SDK filename."""

    def __init__(self, sdk_filename: str) -> None:
        super().__init__(f"Invalid SDK filename {sdk_filename!r}.")


class RepeatedPlatformError(CraftPlatformsError):
    """Error when multiple platforms have the same build-for base and architecture."""

    def __init__(
        self,
        platforms: Iterable[str],
    ) -> None:
        bf_platforms = ",".join(platforms)
        super().__init__(
            message="Multiple platforms target the same base and architecture.",
            details=f"Same build-for defined in platforms: {bf_platforms}.",
            resolution="Provide only one platform per build-for value.",
        )


class LinterError(SdkcraftError):
    """SDK linting returned an error."""

    def __init__(self, status: int, *, resolution: str | None = None) -> None:
        self.retcode = status
        super().__init__("Linter errors found!", resolution=resolution)


class ShellCheckError(SdkcraftError):
    """ShellCheck returned an error."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Cannot run shellcheck: {message}")


class SpreadFileMissingError(SdkcraftError, FileNotFoundError):
    """Error finding spread project file."""
