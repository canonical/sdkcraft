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

from pydantic import BaseModel
from sdkcraft.models.located import Located, Unmarked
from sdkcraft.models.marked import MarkedLoader

YAML_FILE = """\
flow_scalar: a ⚽ ccc
block_scalar: |
  aaa
  bb
  c
flow_list: [a, bb, ccc]
block_list:
  - aaa
  - bb
  - c
flow_map: {a: 1, bb: 22, ccc: 333}
block_map:
  aaa: 111
  bb: 22
  c: 3
"""


class Model(BaseModel):
    flow_scalar: Located[str]
    block_scalar: Located[str]
    flow_list: Located[list[Located[str]]]
    block_list: Located[list[Located[str]]]
    flow_map: Located[dict[Unmarked[str], Located[int]]]
    block_map: Located[dict[Unmarked[str], Located[int]]]


def test_validate():
    value = MarkedLoader.load(YAML_FILE)
    model = Model.model_validate(value)

    assert model.flow_scalar.value == "a ⚽ ccc"
    assert _location(model.flow_scalar) == [1, 1, 14, 20]

    assert model.block_scalar.value == "aaa\nbb\nc\n"
    assert _location(model.block_scalar) == [2, 6, 15, 0]

    flow_list = [v.value for v in model.flow_list.value]
    assert flow_list == ["a", "bb", "ccc"]
    assert _location(model.flow_list) == [6, 6, 12, 23]
    assert _location(model.flow_list.value[0]) == [6, 6, 13, 13]
    assert _location(model.flow_list.value[1]) == [6, 6, 16, 17]
    assert _location(model.flow_list.value[2]) == [6, 6, 20, 22]

    block_list = [v.value for v in model.block_list.value]
    assert block_list == ["aaa", "bb", "c"]
    assert _location(model.block_list) == [8, 11, 3, 0]
    assert _location(model.block_list.value[0]) == [8, 8, 5, 7]
    assert _location(model.block_list.value[1]) == [9, 9, 5, 6]
    assert _location(model.block_list.value[2]) == [10, 10, 5, 5]

    flow_map = {k: v.value for k, v in model.flow_map.value.items()}
    assert flow_map == {"a": 1, "bb": 22, "ccc": 333}
    assert _location(model.flow_map) == [11, 11, 11, 34]
    assert _location(model.flow_map.value["a"]) == [11, 11, 15, 15]
    assert _location(model.flow_map.value["bb"]) == [11, 11, 22, 23]
    assert _location(model.flow_map.value["ccc"]) == [11, 11, 31, 33]

    block_map = {k: v.value for k, v in model.block_map.value.items()}
    assert block_map == {"aaa": 111, "bb": 22, "c": 3}
    assert _location(model.block_map) == [13, 16, 3, 0]
    assert _location(model.block_map.value["aaa"]) == [13, 13, 8, 10]
    assert _location(model.block_map.value["bb"]) == [14, 14, 7, 8]
    assert _location(model.block_map.value["c"]) == [15, 15, 6, 6]


class BasicModel(BaseModel):
    one: Located[str]
    two: Unmarked[str]


def test_location_missing():
    model = BasicModel.model_validate({"one": "1", "two": "2"})

    assert model.one.value == "1"
    assert _location(model.one) == [None, None, None, None]
    assert model.two == "2"

    value = MarkedLoader.load("one: '1'\ntwo: '2'\n")
    value["one"].node.end_mark = None
    value["two"].node.end_mark = None
    model = BasicModel.model_validate(value)

    assert model.one.value == "1"
    assert _location(model.one) == [1, None, 6, None]
    assert model.two == "2"

    value["one"].node.start_mark = None
    value["two"].node.start_mark = None
    model = BasicModel.model_validate(value)

    assert model.one.value == "1"
    assert _location(model.one) == [None, None, None, None]
    assert model.two == "2"


def _location[T](value: Located[T]) -> list[int | None]:
    return [
        value.location.line,
        value.location.end_line,
        value.location.column,
        value.location.end_column,
    ]
