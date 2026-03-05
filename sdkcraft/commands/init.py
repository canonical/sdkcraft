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

"""Creation of minimalist SDKcraft projects."""

from __future__ import annotations

import textwrap

from craft_application.commands import init


class InitCommand(init.InitCommand):
    """Initialize an SDKcraft project."""

    name = "init"
    help_msg = "Initialize an SDKcraft project"
    overview = textwrap.dedent(
        """
        Initialize an SDKcraft project by creating an 'sdkcraft.yaml' file
        together with hooks and tests.
        """
    )
    examples: list[tuple[str, str]] = [
        ("Initialize a new project", "sdkcraft init"),
    ]
    related_commands: list[str] | None = None
