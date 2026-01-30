# Copyright 2024 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Tests for shellcheck linting functionality."""

from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
from craft_cli import CraftError
from sdkcraft.commands.lifecycle import _run_shellcheck_on_hooks


def _mock_run_factory(payload: list[dict[str, object]], returncode: int = 1):
    def _mock_run(cmd: list[str], **kwargs):
        return subprocess.CompletedProcess(
            cmd, returncode=returncode, stdout=json.dumps(payload), stderr=""
        )

    return _mock_run


def test_lint_no_hooks_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    hooks_dir = tmp_path / "hooks"
    calls: list[list[str]] = []

    def mock_run(cmd: list[str], **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", mock_run)

    _run_shellcheck_on_hooks(hooks_dir, [])

    assert calls == []


def test_lint_empty_hooks_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    calls: list[list[str]] = []

    def mock_run(cmd: list[str], **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", mock_run)

    _run_shellcheck_on_hooks(hooks_dir, [])

    assert calls == []


def test_lint_warning_non_fatal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "configure").write_text("#!/bin/bash\necho test\n")

    shellcheck_output = [
        {
            "file": "configure",
            "line": 2,
            "column": 1,
            "level": "warning",
            "code": 2034,
            "message": "var appears unused.",
        }
    ]

    monkeypatch.setattr("subprocess.run", _mock_run_factory(shellcheck_output))

    _run_shellcheck_on_hooks(hooks_dir, [])


def test_lint_error_fatal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "configure").write_text("#!/bin/bash\necho test\n")

    shellcheck_output = [
        {
            "file": "configure",
            "line": 2,
            "column": 1,
            "level": "error",
            "code": 1234,
            "message": "Syntax error.",
        }
    ]

    monkeypatch.setattr("subprocess.run", _mock_run_factory(shellcheck_output))

    with pytest.raises(CraftError, match="Shellcheck found errors in hooks scripts"):
        _run_shellcheck_on_hooks(hooks_dir, [])


def test_lint_ignore_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "configure").write_text("#!/bin/bash\necho test\n")

    shellcheck_output = [
        {
            "file": "configure",
            "line": 2,
            "column": 1,
            "level": "warning",
            "code": 2034,
            "message": "var appears unused.",
        }
    ]

    monkeypatch.setattr("subprocess.run", _mock_run_factory(shellcheck_output))

    _run_shellcheck_on_hooks(hooks_dir, ["warning"])


def test_lint_error_2148_non_fatal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "configure").write_text("echo test\n")

    shellcheck_output = [
        {
            "file": "configure",
            "line": 1,
            "column": 1,
            "level": "error",
            "code": 2148,
            "message": "Tips depend on target shell and yours is unknown.",
        }
    ]

    monkeypatch.setattr("subprocess.run", _mock_run_factory(shellcheck_output))

    _run_shellcheck_on_hooks(hooks_dir, [])
