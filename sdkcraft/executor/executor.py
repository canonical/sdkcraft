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
"""SDKcraft action executor."""

from typing import override

from craft_parts import Part, PartInfo
from craft_parts.executor import executor, part_handler

from sdkcraft.executor.part_handler import PartHandler


class Executor(executor.Executor):
    """Execute lifecycle actions."""

    @override
    def __init__(
        self,
        base: executor.Executor,
    ) -> None:
        super().__init__(
            part_list=base._part_list,  # noqa: SLF001
            project_info=base._project_info,  # noqa: SLF001
            extra_build_packages=base._extra_build_packages,  # noqa: SLF001
            extra_build_snaps=base._extra_build_snaps,  # noqa: SLF001
            track_stage_packages=base._track_stage_packages,  # noqa: SLF001
            ignore_patterns=base._ignore_patterns,  # noqa: SLF001
            base_layer_dir=base._overlay_manager.base_layer_dir,  # noqa: SLF001
            base_layer_hash=base._base_layer_hash,  # noqa: SLF001
        )

    @override
    def _create_part_handler(
        self,
        part: Part,
    ) -> part_handler.PartHandler:
        """Instantiate a part handler for a new part."""
        if part.name in self._handler:
            return self._handler[part.name]

        handler = PartHandler(
            part,
            part_info=PartInfo(self._project_info, part),
            part_list=self._part_list,
            track_stage_packages=self._track_stage_packages,
            overlay_manager=self._overlay_manager,
            ignore_patterns=self._ignore_patterns,
            base_layer_hash=self._base_layer_hash,
        )
        self._handler[part.name] = handler

        return handler
