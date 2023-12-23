"""
Combined wire type + value marshaling/unmarshaling.
"""
# TODO better name might be type mapping? or sth. like that.

from abc import ABC
from collections.abc import Set
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Generic, TypeVar, cast

import msgpack

from .wire_format import (
    AttributeWireType,
    ImmutableMsgPackish,
    MaybeUnknownWireType,
    OptionalWireType,
    SetWireType,
    StringWireType,
    Unknown,
)
from .wire_marshaling import (
    AttributeWireTypeMarshaler,
    AttributeWireTypeUnmarshaler,
    DateAsStringWireTypeMarshaler,
    DateAsStringWireTypeUnmarshaler,
    DateTimeAsStringWireTypeMarshaler,
    DateTimeAsStringWireTypeUnmarshaler,
    MaybeUnknownWireTypeMarshaler,
    MaybeUnknownWireTypeUnmarshaler,
    OptionalWireTypeMarshaler,
    OptionalWireTypeUnmarshaler,
    SetWireTypeMarshaler,
    SetWireTypeUnmarshaler,
    StringWireTypeMarshaler,
    StringWireTypeUnmarshaler,
)

M = TypeVar("M", bound=ImmutableMsgPackish, covariant=True)
# yet again, what we really want here W[M], but this needs HKTVs...

T = TypeVar("T")


@dataclass
class WireRepresentation(ABC, Generic[M, T]):
    attribute_wire_type: AttributeWireType[M]
    "*Must* be set by subclasses."
    unmarshaler: AttributeWireTypeUnmarshaler[AttributeWireType[M], T]
    "*Must* be set by subclasses."
    marshaler: AttributeWireTypeMarshaler[AttributeWireType[M], T]
    "*Must* be set by subclasses."

    def unmarshal_value_msgpack(self, value: ImmutableMsgPackish) -> T:
        return self.unmarshaler.unmarshal_msgpack(value)

    def marshal_value_msgpack(self, value: T) -> M:
        # TODO cf. comment on marshal_msgpack
        return cast(M, self.marshaler.marshal_msgpack(value))


@dataclass
class StringWireRepresentation(WireRepresentation[str, str]):
    """
    Trivial string representation.
    """

    attribute_wire_type: StringWireType = field(default=StringWireType())
    unmarshaler: StringWireTypeUnmarshaler = field(
        default=StringWireTypeUnmarshaler()
    )
    marshaler: StringWireTypeMarshaler = field(
        default=StringWireTypeMarshaler()
    )


@dataclass
class DateTimeAsStringWireRepresentation(WireRepresentation[str, datetime]):
    """
    Representation converting a datetime to a string.
    """

    attribute_wire_type: StringWireType = field(default=StringWireType())
    unmarshaler: DateTimeAsStringWireTypeUnmarshaler = field(
        default=DateTimeAsStringWireTypeUnmarshaler()
    )
    marshaler: DateTimeAsStringWireTypeMarshaler = field(
        default=DateTimeAsStringWireTypeMarshaler()
    )


@dataclass
class DateAsStringWireRepresentation(WireRepresentation[str, date]):
    """
    Representation converting a date to a string.
    """

    attribute_wire_type: StringWireType = field(default=StringWireType())
    unmarshaler: DateAsStringWireTypeUnmarshaler = field(
        default=DateAsStringWireTypeUnmarshaler()
    )
    marshaler: DateAsStringWireTypeMarshaler = field(
        default=DateAsStringWireTypeMarshaler()
    )


@dataclass
class OptionalWireRepresentation(WireRepresentation[M | None, T | None]):
    """
    Wrapper around another representation to make it allow null values.
    """

    inner: WireRepresentation[M, T]
    attribute_wire_type: OptionalWireType[M]
    unmarshaler: OptionalWireTypeUnmarshaler[M, T]
    marshaler: OptionalWireTypeMarshaler[M, T]

    def __init__(self, inner: WireRepresentation[M, T]):
        self.inner = inner
        # wire type is same as inner repr's because wire values are all
        # implicitly nullable:
        self.attribute_wire_type = OptionalWireType(inner.attribute_wire_type)
        self.unmarshaler = OptionalWireTypeUnmarshaler(inner.unmarshaler)
        self.marshaler = OptionalWireTypeMarshaler(inner.marshaler)


@dataclass
class MaybeUnknownWireRepresentation(
    WireRepresentation[M | msgpack.ExtType, T | Unknown]
):
    """
    Wrapper around another representation to make it allow unknown values.
    """

    inner: WireRepresentation[M, T]
    attribute_wire_type: MaybeUnknownWireType[M]
    unmarshaler: MaybeUnknownWireTypeUnmarshaler[M, T]
    marshaler: MaybeUnknownWireTypeMarshaler[M, T]

    def __init__(self, inner: WireRepresentation[M, T]):
        self.inner = inner
        # wire type is same as inner repr's because wire values are all
        # implicitly unknown-able:
        self.attribute_wire_type = MaybeUnknownWireType(
            inner.attribute_wire_type
        )
        self.unmarshaler = MaybeUnknownWireTypeUnmarshaler(inner.unmarshaler)
        self.marshaler = MaybeUnknownWireTypeMarshaler(inner.marshaler)


@dataclass
class SetWireRepresentation(WireRepresentation[list[M], Set[T]]):
    """
    Wrapper around another representation representing a set of its values.
    """

    inner: WireRepresentation[M, T]
    attribute_wire_type: SetWireType[M]
    unmarshaler: SetWireTypeUnmarshaler[M, T]
    marshaler: SetWireTypeMarshaler[M, T]

    def __init__(self, inner: WireRepresentation[M, T]):
        self.inner = inner
        self.attribute_wire_type = SetWireType(inner.attribute_wire_type)
        self.unmarshaler = SetWireTypeUnmarshaler(inner.unmarshaler)
        self.marshaler = SetWireTypeMarshaler(inner.marshaler)
