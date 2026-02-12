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
from typing import TYPE_CHECKING

from craft_cli import emit
from rich.text import Text

from sdkcraft.linters.interfaces import InterfaceCheck
from sdkcraft.linters.shellcheck import ShellCheck
from sdkcraft.models import LinterIssue, LinterResult, Location, MarkedProject

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


def run_linters(prime_dir: Path, project: MarkedProject) -> list[LinterIssue]:
    """Run all linters on the SDK at the given path."""
    emit.progress("Running linters...")

    issues = [
        ShellCheck().run(prime_dir / "sdk"),
        InterfaceCheck().run(prime_dir, project),
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
    code = "" if issue.code is None else issue.code

    return (issue.path, _location_key(issue.location), issue.linter, code)


def _location_key(location: Location) -> list[int]:
    return [
        0 if n is None else n
        for n in (
            location.line,
            location.column,
            location.end_line,
            location.end_column,
        )
    ]


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
    rows = _resolve_end(issue.location.line, issue.location.end_line)
    columns = _resolve_end(issue.location.column, issue.location.end_column)

    location = ""
    if rows is not None:
        # Edge case: PyYAML can report end_column=0, which means the actual
        # end was on the previous line, but it forgot how long the line was.
        if columns is not None and columns[1] == 0:
            rows = (rows[0], rows[1] - 1)

        if rows[1] > rows[0]:
            location = f" lines {rows[0]}-{rows[1]}"
        else:
            location = f" line {rows[0]}"

    lines = [
        f"In {issue.path}{location} [{issue.linter} {issue.result}]\n",
        issue.message + "\n",
    ]

    if issue.abspath is not None and rows is not None:
        with issue.abspath.open() as f:
            section = list(islice(f, rows[0] - 1, rows[1]))

        if len(section) == 1 and columns is not None:
            # PyYAML edge case again.
            if columns[1] == 0:
                columns = (columns[0], len(section[-1]))

            spaces = _cell_len(section[-1][: columns[0] - 1])
            carets = _cell_len(section[-1][columns[0] - 1 : columns[1]])
            section.append(" " * spaces + "^" * carets + "\n")

        lines.extend(f"  {line}" if line else "" for line in section)

    if issue.url is not None:
        lines.append(f"More information: {issue.url}\n")

    return "".join(lines)


def _resolve_end(start: int | None, end: int | None) -> tuple[int, int] | None:
    if start is None:
        return None

    if end is None:
        return (start, start)

    return (start, end)


def _cell_len(text: str) -> int:
    return Text(text).cell_len


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
