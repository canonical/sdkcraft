# This file is part of sdkcraft.
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
"""Tests for environment variable parsing."""

from __future__ import annotations

from unicodedata import category

import pytest
from sdkcraft.env import parse_systemctl_environment

SYSTEMCTL_ESCAPES = {
    "\a": r"\a",
    "\b": r"\b",
    "\f": r"\f",
    "\n": r"\n",
    "\r": r"\r",
    "\t": r"\t",
    "\v": r"\v",
    "\\": r"\\",
    "'": r"\'",
}


@pytest.mark.parametrize(
    ("text", "environ"),
    [
        ("K=V\n", {"K": "V"}),
        ("K=V=V=V\n", {"K": "V=V=V"}),
        ("K1=V1\nK2=V2\n", {"K1": "V1", "K2": "V2"}),
    ],
)
def test_parse_systemctl_environment(text: str, environ: dict[str, str]):
    assert parse_systemctl_environment(text) == environ


def test_parse_systemctl_environment_escaped():
    raw = []
    escapes = []
    for c in map(chr, range(0x80)):
        raw.append(c)
        escape = SYSTEMCTL_ESCAPES.get(c)
        if escape:
            escapes.append(escape)
        elif category(c).startswith("C"):
            escapes.append(rf"\{ord(c):03o}")
        else:
            escapes.append(c)

    text = f"K=$'{''.join(escapes)}'"
    environ = {"K": "".join(raw)}
    assert parse_systemctl_environment(text) == environ


def test_parse_systemctl_environment_not_key_value():
    with pytest.raises(ValueError, match="invalid environment entry 'KEY'"):
        parse_systemctl_environment("KEY\n")


def test_parse_systemctl_environment_empty_key():
    with pytest.raises(ValueError, match="empty environment variable name in '=VALUE'"):
        parse_systemctl_environment("=VALUE\n")


def test_parse_systemctl_environment_duplicate_key():
    with pytest.raises(ValueError, match="duplicate environment variable 'K'"):
        parse_systemctl_environment("K=1\nK=2\n")


def test_parse_systemctl_environment_unterminated():
    with pytest.raises(ValueError, match='invalid environment entry "K=\\$\'1"'):
        parse_systemctl_environment("K=$'1\n")


def test_parse_systemctl_environment_invalid_escape():
    with pytest.raises(
        ValueError, match='invalid environment entry "K=\\$\'1\\\\\\\\"'
    ):
        parse_systemctl_environment("K=$'1\\\n")
