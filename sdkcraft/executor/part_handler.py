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
"""SDKcraft part step handler."""

from typing import override

from craft_parts.executor import part_handler
from craft_parts.packages import Repository
from craft_parts.packages.deb import Ubuntu
from craft_parts.utils import file_utils


class PartHandler(part_handler.PartHandler):
    """Execute lifecycle actions."""

    @override
    def _unpack_stage_packages(self) -> None:
        if not issubclass(Repository, Ubuntu):
            raise NotImplementedError(
                "stage-packages only supported for Debian-based platforms"
            )

        target = self._part.part_install_dir / "var" / "cache" / "apt" / "archives"
        target.mkdir(exist_ok=True, parents=True)
        for pkg in self._part.part_packages_dir.glob("*.deb"):
            file_utils.link_or_copy(str(pkg), str(target / pkg.name))
