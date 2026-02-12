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
"""Tests for YAML utilities."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sdkcraft.models.marked import (
    MarkedDict,
    MarkedHashable,
    MarkedList,
    MarkedLoader,
    MarkedSet,
)
from yaml import MappingNode, ScalarNode, SequenceNode

YAML_FILE = """\
list:
  - 2006-01-02 15:04:05.999999+07:00
  - !!set {a, b, c, d}
pairs: !!pairs
  - x: true
scalar: 1.5
"""


def test_marked_hashable():
    a = MarkedLoader.load("'a'")
    assert isinstance(a, MarkedHashable)
    assert a == "a"
    assert "a" == a  # noqa: SIM300
    assert a != "b"
    assert "b" != a  # noqa: SIM300

    b = MarkedLoader.load("'b'")
    assert isinstance(b, MarkedHashable)
    assert a != b
    assert b != a

    a2 = MarkedLoader.load(" 'a'")
    assert isinstance(a2, MarkedHashable)
    assert a2.node.start_mark.column != a.node.start_mark.column
    assert a == a2
    assert a2 == a

    d: dict[Any, int] = {"a": -1}
    for i, k in enumerate((a, a2, "a")):
        d[k] = i
        assert len(d) == 1
        assert d["a"] == i
        assert d[a] == i
        assert d[a2] == i

    assert len({"a", a, a2}) == 1


def test_marked_loader():
    mapping = MarkedLoader.load(YAML_FILE)
    assert isinstance(mapping, MarkedDict)
    assert isinstance(mapping.node, MappingNode)
    assert len(mapping.node.value) == 3

    for k in mapping:
        assert isinstance(k, MarkedHashable)
        assert isinstance(k.node, ScalarNode)
        assert type(k.value) is str
    assert {k.value for k in mapping} == {"list", "pairs", "scalar"}

    sequence = mapping["list"]
    assert isinstance(sequence, MarkedList)
    assert isinstance(sequence.node, SequenceNode)
    assert len(sequence.node.value) == 2

    date = sequence[0]
    assert isinstance(date, MarkedHashable)
    assert isinstance(date.node, ScalarNode)
    assert type(date.value) is datetime

    abcd = sequence[1]
    assert isinstance(abcd, MarkedSet)
    assert isinstance(abcd.node, MappingNode)
    assert len(abcd.node.value) == 4

    for s in abcd:
        assert isinstance(s, MarkedHashable)
        assert isinstance(s.node, ScalarNode)
        assert type(s.value) is str
    assert {s.value for s in abcd} == {"a", "b", "c", "d"}

    pairs = mapping["pairs"]
    assert isinstance(pairs, MarkedList)
    assert isinstance(pairs.node, SequenceNode)
    assert len(pairs.node.value) == 1

    pair = pairs[0]
    assert type(pair) is tuple

    assert isinstance(pair[0], MarkedHashable)
    assert isinstance(pair[0].node, ScalarNode)
    assert type(pair[0].value) is str

    assert isinstance(pair[1], MarkedHashable)
    assert isinstance(pair[1].node, ScalarNode)
    assert type(pair[1].value) is bool

    scalar = mapping["scalar"]
    assert isinstance(scalar, MarkedHashable)
    assert isinstance(scalar.node, ScalarNode)
    assert type(scalar.value) is float
