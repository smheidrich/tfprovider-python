from collections.abc import Iterable
from dataclasses import dataclass
from typing import Self

from tfplugin_proto import tfplugin6_4_pb2 as pb


class AttributePathElement:
    pass


@dataclass(frozen=True)
class AttributeName(AttributePathElement):
    name: str


@dataclass(frozen=True)
class ElementKey(AttributePathElement):
    key: str | int


class AttributePath:
    def __init__(self, from_: Iterable[AttributePathElement]):
        self._elements = tuple(from_)

    def attribute_name(self, name: str, /) -> Self:
        return self.__class__(self._elements + (AttributeName(name),))

    def element_key(self, key: str | int, /) -> Self:
        return self.__class__(self._elements + (ElementKey(key),))

    def to_protobuf(self) -> pb.AttributePath:
        steps = []
        for elem in self._elements:
            match elem:
                case AttributeName(name):
                    steps.append(pb.AttributePath.Step(attribute_name=name))
                case ElementKey(str(key)):
                    steps.append(pb.AttributePath.Step(element_key_string=key))
                case ElementKey(int(key)):
                    steps.append(pb.AttributePath.Step(element_key_int=key))
                case _:
                    raise TypeError("should never happen")
        return pb.AttributePath(steps=steps)

    def __str__(self) -> str:
        elem_strs = []
        for elem in self._elements:
            match elem:
                case AttributeName(name):
                    elem_strs.append(f".{name}")
                case ElementKey(key):
                    elem_strs.append(f"[{key!r}]")
                case _:
                    raise TypeError("should never happen")
        return "".join(elem_strs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({list(self._elements)!r})"


ROOT = AttributePath(tuple())
