# Copyright 2026 Canonical Ltd.
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

"""Formatting helpers for SDKcraft commands."""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

from rich.text import Text

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from sdkcraft.models.store import SdkChannelMapModel, SdkRevisionModel


def _format_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
) -> list[str]:
    """Render rows as a plain aligned table."""
    if not rows:
        return []

    widths = [
        max(map(_cell_len, itertools.chain([header], (row[index] for row in rows))))
        for index, header in enumerate(headers)
    ]

    lines = [_format_table_row(headers, widths)]
    lines.extend(_format_table_row(row, widths) for row in rows)
    return lines


def _format_table_row(values: Sequence[str], widths: list[int]) -> str:
    return "  ".join(
        _align_left(value, width) for value, width in zip(values, widths, strict=True)
    )


def _align_left(value: str, width: int) -> str:
    text = Text(value)
    text.align("left", width)
    return text.plain


def _cell_len(value: str) -> int:
    return Text(value).cell_len


def _format_uploaded(uploaded: datetime | None) -> str:
    if uploaded is None:
        return "-"
    return uploaded.isoformat(timespec="seconds").replace("+00:00", "Z")


def _format_architectures(
    revision: SdkRevisionModel,
    fallback_architectures: Sequence[str],
) -> str:
    architectures = sorted(
        {base.architecture for base in revision.bases} | set(fallback_architectures)
    )

    return ",".join(architectures) or "-"


def _format_channels(channels: list[str]) -> str:
    if not channels:
        return "-"
    return ",".join(channels)


def format_channel_map(channel_map: list[SdkChannelMapModel]) -> list[str]:
    """Render channel map entries as a plain aligned table."""
    rows = [(entry.channel, str(entry.revision)) for entry in channel_map]
    return _format_table(("CHANNEL", "REVISION"), rows)


def format_revisions(
    revisions: list[SdkRevisionModel],
    channel_map: list[SdkChannelMapModel],
) -> list[str]:
    """Render revision entries as a plain aligned table."""
    channels_by_revision: dict[int, list[str]] = {}
    architectures_by_revision: dict[int, list[str]] = {}
    for entry in channel_map:
        channels_by_revision.setdefault(entry.revision, []).append(entry.channel)
        architectures_by_revision.setdefault(entry.revision, []).append(
            entry.base.architecture
        )

    rows = [
        (
            _format_channels(channels_by_revision.get(revision.revision, [])),
            str(revision.revision),
            _format_architectures(
                revision,
                architectures_by_revision.get(revision.revision, []),
            ),
            _format_uploaded(revision.created_at),
        )
        for revision in revisions
    ]
    return _format_table(("CHANNEL", "REVISION", "ARCHITECTURE", "UPLOADED"), rows)
