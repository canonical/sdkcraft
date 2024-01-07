#  This file is part of craftcraft.
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

from craftcraft import Craftcraft, application, services


def main() -> int:
    """Start up and run Craftcraft."""
    factory = services.ServiceFactory(
        app=application.APP_METADATA,
        LifecycleClass=services.Lifecycle,
        PackageClass=services.Package,
    )

    app = Craftcraft(app=application.APP_METADATA, services=factory)

    return app.run()
