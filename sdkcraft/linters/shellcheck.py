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
"""ShellCheck linter implementation."""

from __future__ import annotations

import subprocess
from itertools import groupby
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, HttpUrl
from pydantic.alias_generators import to_camel

from sdkcraft.errors import ShellCheckError
from sdkcraft.models import LinterIssue, LinterResult

HOOKS = (
    "setup-base",
    "setup-project",
    "save-state",
    "restore-state",
    "check-health",
)


class ShellCheckModel(BaseModel):
    """Base class for ShellCheck JSON1 data types."""

    model_config = ConfigDict(alias_generator=to_camel)


class Replacement(ShellCheckModel):
    """ShellCheck text replacement."""

    precedence: int
    insertion_point: Literal["beforeStart", "afterEnd"]
    line: int
    end_line: int
    column: int
    end_column: int
    replacement: str


class Fix(ShellCheckModel):
    """ShellCheck automated fixes."""

    replacements: list[Replacement]


class PositionedComment(ShellCheckModel):
    """ShellCheck issue."""

    file: Path
    line: int
    end_line: int
    column: int
    end_column: int
    level: Literal["style", "info", "warning", "error"]
    code: int
    message: str
    fix: Fix | None


class JSON1(ShellCheckModel):
    """ShellCheck JSON1 output."""

    comments: list[PositionedComment]


class ShellCheck:
    """ShellCheck linter for SDK hooks."""

    def run(self, path: Path) -> list[LinterIssue]:
        """Run shellcheck on the given SDK's hooks."""
        hooks = [Path("hooks", hook) for hook in HOOKS]
        args = [str(hook) for hook in hooks if (path / hook).is_file()]
        if not args:
            return []

        command = [
            "shellcheck",
            "--check-sourced",
            "--external-sources",
            "--format=json1",
            "--norc",
            "--shell=bash",
            *args,
        ]

        process = subprocess.run(
            command, capture_output=True, check=False, cwd=path, text=True
        )
        if process.returncode > 1:
            raise ShellCheckError(process.stderr)
        output = JSON1.model_validate_json(process.stdout)

        _workaround_issue_3397(output)

        return [_comment_as_issue(path, comment) for comment in output.comments]


def _workaround_issue_3397(output: JSON1) -> None:
    output.comments.sort(key=_comment_key)
    output.comments = [comment for comment, _ in groupby(output.comments)]


ReplacementKey = tuple[int, str, list[int], str]
FixKey = list[ReplacementKey]
CommentKey = tuple[Path, list[int], str, int, str, bool, FixKey]


def _comment_key(comment: PositionedComment) -> CommentKey:
    return (
        comment.file,
        [comment.line, comment.end_line, comment.column, comment.end_column],
        comment.level,
        comment.code,
        comment.message,
        comment.fix is not None,
        [] if comment.fix is None else _fix_key(comment.fix),
    )


def _fix_key(fix: Fix) -> FixKey:
    return [_replacement_key(replacement) for replacement in fix.replacements]


def _replacement_key(replacement: Replacement) -> ReplacementKey:
    return (
        replacement.precedence,
        replacement.insertion_point,
        [
            replacement.line,
            replacement.end_line,
            replacement.column,
            replacement.end_column,
        ],
        replacement.replacement,
    )


def _comment_as_issue(path: Path, comment: PositionedComment) -> LinterIssue:
    match comment.level:
        case "style" | "info":
            result = LinterResult.ISSUE
        case "warning":
            result = LinterResult.WARNING
        case "error":
            result = LinterResult.ERROR

    return LinterIssue(
        linter="shellcheck",
        code=f"SC{comment.code:04}",
        result=result,
        message=comment.message,
        url=HttpUrl(f"https://www.shellcheck.net/wiki/SC{comment.code:04}"),
        path=comment.file,
        abspath=path / comment.file,
        line=comment.line,
        end_line=comment.end_line,
        column=comment.column,
        end_column=comment.end_column - 1,
    )
