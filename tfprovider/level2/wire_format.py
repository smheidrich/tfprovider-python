"""
Terraform "object wire format", as documented in:
https://github.com/hashicorp/terraform/blob/bdc38b6527ee9927cee67cc992e02cc199f3cae1/docs/plugin-protocol/object-wire-format.md
"""
import json
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Generic, TypeAlias, TypeVar

import msgpack


@dataclass(frozen=True)
class Unknown:
    pass


@dataclass(frozen=True)
class UnrefinedUnknown(Unknown):
    pass


@dataclass(frozen=True)
class RefinedUnknown(Unknown):
    pass


JsonishNotNonePrimitives: TypeAlias = str | int | float | bool

JsonishPrimitives: TypeAlias = JsonishNotNonePrimitives | None

ImmutableJsonish: TypeAlias = (
    Mapping[str, "ImmutableJsonish"]
    | Sequence["ImmutableJsonish"]
    | JsonishPrimitives
)

ImmutableJsonishWithUnknown: TypeAlias = (
    Mapping[str, "ImmutableJsonishWithUnknown"]
    | Sequence["ImmutableJsonishWithUnknown"]
    | JsonishPrimitives
    | Unknown
)

ImmutableMsgPackish: TypeAlias = (
    Mapping[str, "ImmutableMsgPackish"]
    | Sequence["ImmutableMsgPackish"]
    | JsonishPrimitives
    | msgpack.ExtType
)

F = TypeVar("F")
T = TypeVar("T")

# types

M = TypeVar("M", bound=ImmutableMsgPackish, covariant=True)


class AttributeWireType(ABC, Generic[M]):

    marshaled_value_type: type[M]
    """
    The type of marshaled values conforming to this type.

    To be set by subclasses.
    """

    def serialize_type(self) -> bytes:
        return json.dumps(self.marshal_type()).encode("utf-8")

    @abstractmethod
    def marshal_type(self) -> ImmutableJsonish:
        pass


class StringWireType(AttributeWireType[str]):
    marshaled_value_type = str

    def marshal_type(self) -> str:
        return "string"


class NumberWireType(AttributeWireType[int | float | str]):
    marshaled_value_type = int | float | str

    def marshal_type(self) -> str:
        return "number"


class BoolWireType(AttributeWireType[bool]):
    marshaled_value_type = bool

    def marshal_type(self) -> str:
        return "bool"


# TODO what we really want (but needs HKTVs
#   https://github.com/python/typing/issues/548):
# W = TypeVar("W", bound=AttributeWireType[M])


class OptionalWireType(AttributeWireType[M | None]):
    marshaled_value_type: type[M | None]

    def __init__(self, inner_attribute_type: AttributeWireType[M]):
        self.inner_attribute_type = inner_attribute_type

    def marshal_type(self) -> ImmutableJsonish:
        # all wire types are implicitly nullable so we return this unmodified:
        return self.inner_attribute_type.marshal_type()


class MaybeUnknownWireType(AttributeWireType[M | msgpack.ExtType]):
    marshaled_value_type: type[M | msgpack.ExtType]

    def __init__(self, inner_attribute_type: AttributeWireType[M]):
        self.inner_attribute_type = inner_attribute_type

    def marshal_type(self) -> ImmutableJsonish:
        # all wire types are (AFAICT) implicitly unknown-able so we return this
        # unmodified:
        return self.inner_attribute_type.marshal_type()


class ListWireType(AttributeWireType[list[M]]):
    marshaled_value_type: type[list[M]]

    def __init__(self, inner_attribute_type: AttributeWireType[M]):
        self.inner_attribute_type = inner_attribute_type

    def marshal_type(self) -> list[ImmutableJsonish]:
        return ["list", self.inner_attribute_type.marshal_type()]


class SetWireType(AttributeWireType[list[M]]):
    marshaled_value_type: type[list[M]]

    def __init__(self, inner_attribute_type: AttributeWireType[M]):
        self.inner_attribute_type = inner_attribute_type

    def marshal_type(self) -> list[ImmutableJsonish]:
        return ["set", self.inner_attribute_type.marshal_type()]


class MapWireType(AttributeWireType[dict[str, M]]):
    marshaled_value_type: type[dict[str, M]]

    def __init__(self, inner_attribute_type: AttributeWireType[M]):
        self.inner_attribute_type = inner_attribute_type

    def marshal_type(self) -> list[ImmutableJsonish]:
        return ["map", self.inner_attribute_type.marshal_type()]
