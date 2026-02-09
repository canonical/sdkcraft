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
"""Marked objects which remember YAML metadata."""

from abc import ABC, abstractmethod
from collections.abc import Hashable
from typing import Any, BinaryIO, TextIO, override

from yaml import Node, SafeLoader, load


class Marked[T](ABC):
    """Holds an object together with the YAML node it came from."""

    @property
    @abstractmethod
    def value(self) -> T:
        """Access the unmarshaled object."""

    @property
    @abstractmethod
    def node(self) -> Node:
        """Access the YAML node which encodes the object."""


class MarkedAny[T](Marked[T]):
    """Holds a generic object together with the YAML node it came from."""

    __slots__ = ("_value", "_node")

    def __init__(self, value: T, node: Node) -> None:
        self._value = value
        self._node = node

    @property
    @override
    def value(self) -> T:
        return self._value

    @property
    @override
    def node(self) -> Node:
        return self._node

    def __repr__(self) -> str:
        return repr(self._value)


class MarkedHashable[T: Hashable](MarkedAny[T]):
    """Holds a hashable object together with the YAML node it came from.

    Behaves like the object when used as a dict key or set element.
    """

    def __hash__(self) -> int:
        return self.value.__hash__()

    @override
    def __eq__(self, value: object, /) -> bool:
        if isinstance(value, Marked):
            return self.value == value.value  # type: ignore[no-any-return]

        return self.value.__eq__(value)


class MarkedDict[K, V](dict[K, V], Marked[dict[K, V]]):
    """Holds a dict together with the YAML node it came from.

    Behaves like an ordinary dict with additional attributes.
    """

    __slots__ = ("_node",)

    def __init__(self, value: dict[K, V], node: Node) -> None:
        super().__init__(value)
        self._node = node

    @property
    @override
    def value(self) -> dict[K, V]:
        return self

    @property
    @override
    def node(self) -> Node:
        return self._node


class MarkedList[T](list[T], Marked[list[T]]):
    """Holds a list together with the YAML node it came from.

    Behaves like an ordinary list with additional attributes.
    """

    __slots__ = ("_node",)

    def __init__(self, value: list[T], node: Node) -> None:
        super().__init__(value)
        self._node = node

    @property
    @override
    def value(self) -> list[T]:
        return self

    @property
    @override
    def node(self) -> Node:
        return self._node


class MarkedSet[T](set[T], Marked[set[T]]):
    """Holds a set together with the YAML node it came from.

    Behaves like an ordinary set with additional attributes.
    """

    __slots__ = ("_node",)

    def __init__(self, value: set[T], node: Node) -> None:
        super().__init__(value)
        self._node = node

    @property
    @override
    def value(self) -> set[T]:
        return self

    @property
    @override
    def node(self) -> Node:
        return self._node


class MarkedLoader(SafeLoader):
    """YAML loader that associates nodes with loaded objects.

    Most primitive objects are loaded as MarkedHashable. Sequences and sets are
    loaded as MarkedList and MarkedSet respectively. Mappings are loaded as
    MarkedDict or a MarkedList of key-value pairs.
    """

    @override
    def construct_document(self, node: Any) -> Any:
        """Construct a Python object hierarchy and attach original YAML nodes.

        Collections and hashable objects are copied into special Marked classes
        to improve ergonomics (especially for Pydantic validation).
        """
        value = super().construct_document(node)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        return _specialize(value)

    @override
    def construct_object(self, node: Any, deep: bool = False) -> Any:
        """Construct a Python object and attach the YAML node it came from.

        Collections remain as-is to account for lazy construction.
        """
        value = super().construct_object(node, deep)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        if isinstance(node, Node):
            return MarkedAny[Any](value, node)
        return value  # pyright: ignore[reportUnknownVariableType]

    @classmethod
    def load(cls, stream: str | bytes | TextIO | BinaryIO) -> Any:  # noqa: ANN401
        """Parse the first YAML document in a stream."""
        return load(stream, cls)  # noqa: S506


def _specialize(value: Any) -> Any:  # noqa: ANN401
    if isinstance(value, Marked):
        return _specialize_marked(value.value, value.node)  # pyright: ignore[reportUnknownMemberType]

    if isinstance(value, dict):
        return {_specialize(k): _specialize(v) for k, v in value.items()}  # pyright: ignore[reportUnknownVariableType]
    if isinstance(value, list):
        return [_specialize(v) for v in value]  # pyright: ignore[reportUnknownVariableType]
    if isinstance(value, set):
        return {_specialize(v) for v in value}  # pyright: ignore[reportUnknownVariableType]
    if isinstance(value, tuple):
        return tuple(_specialize(v) for v in value)  # pyright: ignore[reportUnknownVariableType]

    raise AssertionError


def _specialize_marked(value: Any, node: Node) -> Any:  # noqa: ANN401
    if isinstance(value, dict):
        return MarkedDict[Any, Any](_specialize(value), node)
    if isinstance(value, list):
        return MarkedList[Any](_specialize(value), node)
    if isinstance(value, set):
        return MarkedSet[Any](_specialize(value), node)

    if isinstance(value, Hashable):
        return MarkedHashable[Any](value, node)

    return MarkedAny[Any](value, node)
