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
"""Tests for linters."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pydantic import HttpUrl
from sdkcraft.linters.linters import LinterStatus, format_issue, format_summary
from sdkcraft.models import LinterIssue, LinterResult, Location

SETUP_PROJECT = """\
#!/bin/bash

set -x

cat >>'~/.profile' <<'EOF'
PATH="/opt/bin:$PATH"
EOF

echo '⚽' >'~/file'
"""

MULTI_COLUMN = """\
In hooks/setup-project line 5 [shellcheck warning]
Tilde does not expand in quotes. Use $HOME.
  cat >>'~/.profile' <<'EOF'
        ^^^^^^^^^^^^
More information: https://www.shellcheck.net/wiki/SC2088
"""

ONE_COLUMN = """\
In hooks/setup-project line 5 [shellcheck warning]
Tilde does not expand in quotes. Use $HOME.
  cat >>'~/.profile' <<'EOF'
         ^
More information: https://www.shellcheck.net/wiki/SC2088
"""

NO_COLUMN = """\
In hooks/setup-project line 5 [shellcheck warning]
Tilde does not expand in quotes. Use $HOME.
  cat >>'~/.profile' <<'EOF'
More information: https://www.shellcheck.net/wiki/SC2088
"""

MULTI_LINE = """\
In hooks/setup-project lines 5-6 [shellcheck warning]
Tilde does not expand in quotes. Use $HOME.
  cat >>'~/.profile' <<'EOF'
  PATH="/opt/bin:$PATH"
More information: https://www.shellcheck.net/wiki/SC2088
"""

NO_LINE = """\
In hooks/setup-project [shellcheck warning]
Tilde does not expand in quotes. Use $HOME.
More information: https://www.shellcheck.net/wiki/SC2088
"""

NO_FILE = """\
In hooks/setup-project line 5 [shellcheck warning]
Tilde does not expand in quotes. Use $HOME.
More information: https://www.shellcheck.net/wiki/SC2088
"""

NO_URL = """\
In hooks/setup-project line 5 [shellcheck warning]
Tilde does not expand in quotes. Use $HOME.
  cat >>'~/.profile' <<'EOF'
        ^^^^^^^^^^^^
"""

WIDE_COLUMN = """\
In hooks/setup-project line 9 [shellcheck warning]
Tilde does not expand in quotes. Use $HOME.
  echo '⚽' >'~/file'
             ^^^^^^^^
More information: https://www.shellcheck.net/wiki/SC2088
"""


@pytest.mark.parametrize(
    ("model_diff", "location_diff", "text"),
    [
        pytest.param(
            {},
            {},
            MULTI_COLUMN,
            id="multi_column",
        ),
        pytest.param(
            {},
            {"end_line": None},
            MULTI_COLUMN,
            id="implicit_end_line",
        ),
        pytest.param(
            {},
            {"column": 8, "end_column": 8},
            ONE_COLUMN,
            id="one_column",
        ),
        pytest.param(
            {},
            {"column": 8, "end_column": None},
            ONE_COLUMN,
            id="implicit_one_column",
        ),
        pytest.param(
            {},
            {"column": None, "end_column": None},
            NO_COLUMN,
            id="no_column",
        ),
        pytest.param(
            {},
            {"column": None},
            NO_COLUMN,
            id="stray_end_column",
        ),
        pytest.param(
            {},
            {"end_line": 6},
            MULTI_LINE,
            id="multi_line",
        ),
        pytest.param(
            {},
            {"end_line": 6, "column": None},
            MULTI_LINE,
            id="multi_line_no_column",
        ),
        pytest.param(
            {},
            {"end_line": 7, "end_column": 0},
            MULTI_LINE,
            id="multi_line_zero_end_column",
        ),
        pytest.param(
            {},
            {"line": None, "column": None},
            NO_LINE,
            id="no_line",
        ),
        pytest.param(
            {},
            {"line": None},
            NO_LINE,
            id="stray_column",
        ),
        pytest.param(
            {"abspath": None},
            {},
            NO_FILE,
            id="no_abspath",
        ),
        pytest.param(
            {"url": None},
            {},
            NO_URL,
            id="no_url",
        ),
        pytest.param(
            {},
            {"line": 9, "end_line": None, "column": 11, "end_column": 18},
            WIDE_COLUMN,
            id="wide_column",
        ),
    ],
)
def test_format_issue(
    model_diff: dict[str, Any],
    location_diff: dict[str, Any],
    text: str,
    tmp_path_factory: pytest.TempPathFactory,
):
    path = tmp_path_factory.mktemp("sdk")
    hook = path / "hooks" / "setup-project"

    hook.parent.mkdir()
    hook.write_text(SETUP_PROJECT)

    complete = LinterIssue(
        linter="shellcheck",
        result=LinterResult.WARNING,
        message="Tilde does not expand in quotes. Use $HOME.",
        url=HttpUrl("https://www.shellcheck.net/wiki/SC2088"),
        path=hook.relative_to(path),
        abspath=hook,
        location=Location(line=5, end_line=5, column=7, end_column=18),
    )

    diff = model_diff | {"location": complete.location.model_copy(update=location_diff)}
    issue = complete.model_copy(update=diff)
    assert format_issue(issue) == text


@pytest.mark.parametrize(
    ("level", "summary"),
    [
        pytest.param(
            LinterStatus.OK,
            "1 error, 1 warning, 2 issues across 3 files",
            id="ok",
        ),
        pytest.param(
            LinterStatus.WARNINGS,
            "1 error, 1 warning across 2 files",
            id="warnings",
        ),
        pytest.param(
            LinterStatus.ERRORS,
            "1 error in hooks/setup-project",
            id="errors",
        ),
    ],
)
def test_format_summary(level: LinterStatus, summary: str):
    issues = [
        LinterIssue(
            linter="shellcheck",
            result=LinterResult.ISSUE,
            message="",
            path=Path("hooks/check-health"),
        ),
        LinterIssue(
            linter="shellcheck",
            result=LinterResult.ISSUE,
            message="",
            path=Path("hooks/check-health"),
        ),
        LinterIssue(
            linter="shellcheck",
            result=LinterResult.WARNING,
            message="",
            path=Path("hooks/setup-base"),
        ),
        LinterIssue(
            linter="shellcheck",
            result=LinterResult.ERROR,
            message="",
            path=Path("hooks/setup-project"),
        ),
    ]

    assert format_summary(issues, level) == summary
