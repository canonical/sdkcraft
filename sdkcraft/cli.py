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

import logging

from sdkcraft import Sdkcraft, application, services

from . import commands


def _create_app() -> "Sdkcraft":
    # pylint: disable=import-outside-toplevel
    # Import these here so that the script that generates the docs for the
    # commands doesn't need to know *too much* of the application.
    """Start up and run SDKcraft."""
    factory = services.ServiceFactory(
        app=application.APP_METADATA,
        PackageClass=services.Package,
    )

    app = Sdkcraft(app=application.APP_METADATA, services=factory)

    app.add_command_group(
        "Other",
        [
            commands.InitCommand,
        ],
    )

    return app


def main() -> int:
    """Command-line interface entrypoint."""
    # set lib loggers to debug level so that all messages are sent to Emitter
    for lib_name in ("craft_providers", "craft_parts"):
        logger = logging.getLogger(lib_name)
        logger.setLevel(logging.DEBUG)

    app = _create_app()
    return app.run()
