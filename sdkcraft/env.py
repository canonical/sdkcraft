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
"""Environment variable parsing."""

from __future__ import annotations

import codecs
import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


def user_data_path() -> Path:
    """Determine user data directory."""
    # We avoid os.environ for consistency with Workshop, and to workaround
    # https://github.com/microsoft/vscode/issues/237608.
    environ = systemctl_user_environment()
    data_home = environ.get("XDG_DATA_HOME", "")
    if data_home:
        return Path(data_home)
    return Path.home() / ".local" / "share"


def systemctl_user_environment() -> dict[str, str]:
    """Lookup systemd environment for the current real user."""
    env: Mapping[str, str] = os.environ
    sudo_uid = env.get("SUDO_UID")
    euid = os.geteuid()
    if euid != 0:
        uid = euid
    elif sudo_uid is not None:
        try:
            uid = int(sudo_uid)
        except ValueError:
            uid = os.getuid()
    else:
        uid = os.getuid()

    if uid == 0:
        args = []
    elif uid == euid:
        args = ["--user"]
        env = {"XDG_RUNTIME_DIR": f"/run/user/{uid}", **env}
    else:
        args = [f"--machine={uid}@.host", "--user"]

    result = subprocess.run(
        ["systemctl", *args, "show-environment"],
        capture_output=True,
        check=True,
        env=env,
        text=True,
    )

    # TODO: use --output=json once systemd >= 250.  # noqa:FIX002
    return parse_systemctl_environment(result.stdout)


def parse_systemctl_environment(text: str) -> dict[str, str]:
    """Parse environment variables from systemctl output format."""
    lines = text.split("\n")
    if lines and not lines[-1]:
        lines = lines[:-1]

    environ: dict[str, str] = {}

    for line in lines:
        key, sep, value = line.partition("=")
        if not sep:
            raise ValueError(f"invalid environment entry {line!r}")
        if not key:
            raise ValueError(f"empty environment variable name in {line!r}")
        if key in environ:
            raise ValueError(f"duplicate environment variable {key!r}")
        try:
            environ[key] = _parse_systemctl_value(value)
        except ValueError:
            raise ValueError(f"invalid environment entry {line!r}") from None

    return environ


def _parse_systemctl_value(value: str) -> str:
    if not value.startswith("$'"):
        return value
    if not value.endswith("'"):
        raise ValueError

    return codecs.unicode_escape_decode(value[2:-1])[0]
