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
"""Command-line interface entrypoint."""

from __future__ import annotations

import logging

from craft_application.services import ServiceFactory

from sdkcraft.application import APP_METADATA, Sdkcraft
from sdkcraft.commands import (
    CleanCommand,
    InitCommand,
    PackCommand,
    StoreLoginCommand,
    StoreWhoamiCommand,
    TryCommand,
)
from sdkcraft.services import register_sdkcraft_services


def _create_app() -> Sdkcraft:
    register_sdkcraft_services()
    factory = ServiceFactory(APP_METADATA)
    app = Sdkcraft(APP_METADATA, factory)

    app.add_command_group("Lifecycle", [CleanCommand, PackCommand, TryCommand])
    app.add_command_group("Store Account", [StoreLoginCommand, StoreWhoamiCommand])
    app.add_command_group("Other", [InitCommand])

    return app


def main() -> int:
    """Command-line interface entrypoint."""
    # set lib loggers to debug level so that all messages are sent to Emitter
    for lib_name in ("craft_providers", "craft_parts"):
        logger = logging.getLogger(lib_name)
        logger.setLevel(logging.DEBUG)

    app = _create_app()
    return app.run()
