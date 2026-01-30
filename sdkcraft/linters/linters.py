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
"""SDKcraft linter execution and reporting."""

from __future__ import annotations

from collections import Counter
from enum import IntEnum, unique
from functools import partial, reduce
from itertools import chain, groupby, islice
from typing import TYPE_CHECKING, cast

from craft_cli import emit

from sdkcraft.linters.shellcheck import ShellCheck
from sdkcraft.models import LinterIssue, LinterResult

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


@unique
class LinterStatus(IntEnum):
    """Status codes for the linter execution."""

    OK = 0
    ISSUES = 1
    WARNINGS = 2
    ERRORS = 3


def run_linters(path: Path) -> list[LinterIssue]:
    """Run all linters on the SDK at the given path."""
    emit.progress("Running linters...")

    issues = [
        ShellCheck().run(path / "sdk"),
    ]
    return list(chain.from_iterable(issues))


def report(issues: list[LinterIssue], *, intermediate: bool = False) -> LinterStatus:
    """Display the linter report.

    :param issues: The list of issues to display.
    :param intermediate: Set if the linter output is not the main outcome of
        the command execution.
    """
    issues = sorted(issues, key=_issue_key)

    display = partial(emit.progress, permanent=True) if intermediate else emit.message
    if issues:
        summary = format_summary(issues, LinterStatus.OK)
        display(f"Found {summary}:")
        display("")

    for _, group in groupby(issues, lambda issue: issue.path):
        for issue in group:
            display(format_issue(issue))
            display("")
        display("")

    return reduce(_max_status, issues, LinterStatus.OK)


def _issue_key(issue: LinterIssue) -> tuple[Path, list[int], str, str]:
    location = [
        0 if n is None else n
        for n in (issue.line, issue.column, issue.end_line, issue.end_column)
    ]
    code = "" if issue.code is None else issue.code

    return (issue.path, location, issue.linter, code)


def format_summary(issues: Iterable[LinterIssue], level: LinterStatus) -> str:
    """Summarize the given issues by result and file.

    :param issues: The list of issues to summarize, must be nonempty.
    :param level: Issues below this severity will be ignored.
    """
    filtered = [issue for issue in issues if _result_as_status(issue.result) >= level]

    paths = {issue.path for issue in filtered}
    if len(paths) > 1:
        in_files = f"across {len(paths)} files"
    else:
        (path,) = paths
        in_files = f"in {path}"

    counts = Counter(issue.result for issue in filtered)
    results = ", ".join(
        _format_result_count(result, counts[result])
        for result in reversed(LinterResult)
        if counts[result] > 0
    )
    return f"{results} {in_files}"


def _format_result_count(result: LinterResult, count: int) -> str:
    match (result, count):
        case _, n if n <= 1:
            word = str(result)
        case LinterResult.ISSUE | LinterResult.WARNING | LinterResult.ERROR, _:
            word = f"{result}s"

    return f"{count} {word}"


def format_issue(issue: LinterIssue) -> str:
    """Format the given issue as a multiline string."""
    end_line = issue.line if issue.end_line is None else issue.end_line
    end_column = issue.column if issue.end_column is None else issue.end_column

    location = ""
    if issue.line is not None:
        if cast(int, end_line) > issue.line:
            location = f" lines {issue.line}-{end_line}"
        else:
            location = f" line {issue.line}"

    lines = [
        f"In {issue.path}{location} [{issue.linter} {issue.result}]\n",
        issue.message + "\n",
    ]

    if issue.abspath is not None and issue.line is not None:
        with issue.abspath.open() as f:
            section = list(islice(f, issue.line - 1, end_line))

        if len(section) == 1 and issue.column is not None:
            spaces = len(section[-1][: issue.column - 1])
            carets = len(section[-1][issue.column - 1 : end_column])
            section.append(" " * spaces + "^" * carets + "\n")

        lines.extend(f"  {line}" if line else "" for line in section)

    if issue.url is not None:
        lines.append(f"More information: {issue.url}\n")

    return "".join(lines)


def _max_status(status: LinterStatus, issue: LinterIssue) -> LinterStatus:
    return LinterStatus(max(status, _result_as_status(issue.result)))


def _result_as_status(result: LinterResult) -> LinterStatus:
    match result:
        case LinterResult.ERROR:
            return LinterStatus.ERRORS
        case LinterResult.WARNING:
            return LinterStatus.WARNINGS
        case LinterResult.ISSUE:
            return LinterStatus.ISSUES
