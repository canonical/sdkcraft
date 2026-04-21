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

from subprocess import CompletedProcess
from typing import TYPE_CHECKING
from unicodedata import category

import pytest
from sdkcraft.env import parse_systemctl_environment, systemctl_user_environment

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from pytest_mock import MockerFixture, MockType

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


@pytest.fixture
def environ() -> dict[str, str]:
    return {}


@pytest.fixture
def uid() -> int:
    return 0


@pytest.fixture
def euid() -> int:
    return 0


@pytest.fixture
def fake_environ(
    mocker: MockerFixture, environ: dict[str, str]
) -> MutableMapping[str, str]:
    return mocker.patch.dict("os.environ", values=environ, clear=True)


@pytest.fixture
def fake_uid(mocker: MockerFixture, uid: int) -> MockType:
    return mocker.patch("os.getuid", return_value=uid)


@pytest.fixture
def fake_euid(mocker: MockerFixture, euid: int) -> MockType:
    return mocker.patch("os.geteuid", return_value=euid)


@pytest.fixture
def fake_run(mocker: MockerFixture) -> MockType:
    return mocker.patch(
        "sdkcraft.env.subprocess.run",
        return_value=CompletedProcess[str]([], 0, "K=V\n"),
    )


@pytest.mark.usefixtures("fake_uid", "fake_euid")
def test_systemctl_system_environment(
    fake_run: MockType, fake_environ: MutableMapping[str, str]
):
    result = systemctl_user_environment()
    assert result == {"K": "V"}

    fake_run.assert_called_once_with(
        ["systemctl", "show-environment"],
        capture_output=True,
        check=True,
        env=fake_environ,
        text=True,
    )


@pytest.mark.parametrize(
    ("uid", "euid"),
    [(1000, 1000)],
    ids=[pytest.HIDDEN_PARAM],  # type: ignore[list-item]
)
@pytest.mark.usefixtures("fake_uid", "fake_euid")
def test_systemctl_user_environment(
    fake_run: MockType, fake_environ: MutableMapping[str, str]
):
    result = systemctl_user_environment()
    assert result == {"K": "V"}

    fake_run.assert_called_once_with(
        ["systemctl", "--user", "show-environment"],
        capture_output=True,
        check=True,
        env={**fake_environ, "XDG_RUNTIME_DIR": "/run/user/1000"},
        text=True,
    )


@pytest.mark.parametrize(
    "environ",
    [{"SUDO_UID": "1001"}],
    ids=[pytest.HIDDEN_PARAM],  # type: ignore[list-item]
)
@pytest.mark.usefixtures("fake_uid", "fake_euid")
def test_systemctl_sudo_environment(
    fake_run: MockType, fake_environ: MutableMapping[str, str]
):
    result = systemctl_user_environment()
    assert result == {"K": "V"}

    fake_run.assert_called_once_with(
        ["systemctl", "--machine=1001@.host", "--user", "show-environment"],
        capture_output=True,
        check=True,
        env=fake_environ,
        text=True,
    )


@pytest.mark.parametrize(
    ("environ", "uid", "euid"),
    [({"SUDO_UID": "0", "XDG_RUNTIME_DIR": "/custom"}, 1002, 1002)],
    ids=[pytest.HIDDEN_PARAM],  # type: ignore[list-item]
)
@pytest.mark.usefixtures("fake_uid", "fake_euid")
def test_systemctl_sudo_as_user_environment(
    fake_run: MockType, fake_environ: MutableMapping[str, str]
):
    result = systemctl_user_environment()
    assert result == {"K": "V"}

    fake_run.assert_called_once_with(
        ["systemctl", "--user", "show-environment"],
        capture_output=True,
        check=True,
        env=fake_environ,
        text=True,
    )


@pytest.mark.parametrize(
    "environ",
    [{"SUDO_UID": "!@#$%"}],
    ids=[pytest.HIDDEN_PARAM],  # type: ignore[list-item]
)
@pytest.mark.usefixtures("fake_uid", "fake_euid")
def test_systemctl_broken_sudo_environment(
    fake_run: MockType, fake_environ: MutableMapping[str, str]
):
    result = systemctl_user_environment()
    assert result == {"K": "V"}

    fake_run.assert_called_once_with(
        ["systemctl", "show-environment"],
        capture_output=True,
        check=True,
        env=fake_environ,
        text=True,
    )
