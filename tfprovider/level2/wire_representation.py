"""
Combined wire type + value marshaling/unmarshaling.
"""
# TODO better name might be type mapping? or sth. like that.

from abc import ABC
from dataclasses import dataclass, field
from typing import Generic, TypeVar, cast

import msgpack

from .wire_format import (
    AttributeWireType,
    ImmutableJsonishWithUnknown,
    ImmutableMsgPackish,
    MaybeUnknownWireType,
    OptionalWireType,
    StringWireType,
)
from .wire_marshaling import (
    AttributeWireTypeMarshaler,
    AttributeWireTypeUnmarshaler,
    MaybeUnknownWireTypeMarshaler,
    MaybeUnknownWireTypeUnmarshaler,
    OptionalWireTypeMarshaler,
    OptionalWireTypeUnmarshaler,
    StringWireTypeMarshaler,
    StringWireTypeUnmarshaler,
)

M = TypeVar("M", bound=ImmutableMsgPackish)
# yet again, what we really want here W[M], but this needs HKTVs...


@dataclass
class WireRepresentation(ABC, Generic[M]):
    attribute_wire_type: AttributeWireType[M]
    "*Must* be set by subclasses."
    unmarshaler: AttributeWireTypeUnmarshaler[AttributeWireType[M]]
    "*Must* be set by subclasses."
    marshaler: AttributeWireTypeMarshaler[AttributeWireType[M]]
    "*Must* be set by subclasses."

    def unmarshal_value_msgpack(
        self, value: ImmutableMsgPackish
    ) -> ImmutableJsonishWithUnknown:
        return self.unmarshaler.unmarshal_msgpack(value)

    def marshal_value_msgpack(self, value: ImmutableJsonishWithUnknown) -> M:
        # TODO cf. comment on marshal_msgpack
        return cast(M, self.marshaler.marshal_msgpack(value))


@dataclass
class StringWireRepresentation(WireRepresentation[str]):
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
class OptionalWireRepresentation(WireRepresentation[M | None]):
    """
    Wrapper around another representation to make it allow null values.
    """

    inner: WireRepresentation[M]
    attribute_wire_type: AttributeWireType[M | None]
    unmarshaler: OptionalWireTypeUnmarshaler[M | None]
    marshaler: OptionalWireTypeMarshaler[M | None]

    def __init__(self, inner: WireRepresentation[M]):
        self.inner = inner
        # wire type is same as inner repr's because wire values are all
        # implicitly nullable:
        self.attribute_wire_type = OptionalWireType(inner.attribute_wire_type)
        self.unmarshaler = OptionalWireTypeUnmarshaler(inner.unmarshaler)
        self.marshaler = OptionalWireTypeMarshaler(inner.marshaler)


@dataclass
class MaybeUnknownWireRepresentation(WireRepresentation[M | msgpack.ExtType]):
    """
    Wrapper around another representation to make it allow unknown values.
    """

    inner: WireRepresentation[M]
    attribute_wire_type: AttributeWireType[M | msgpack.ExtType]
    unmarshaler: MaybeUnknownWireTypeUnmarshaler[M | msgpack.ExtType]
    marshaler: MaybeUnknownWireTypeMarshaler[M | msgpack.ExtType]

    def __init__(self, inner: WireRepresentation[M]):
        self.inner = inner
        # wire type is same as inner repr's because wire values are all
        # implicitly unknown-able:
        self.attribute_wire_type = MaybeUnknownWireType(
            inner.attribute_wire_type
        )
        self.unmarshaler = MaybeUnknownWireTypeUnmarshaler(inner.unmarshaler)
        self.marshaler = MaybeUnknownWireTypeMarshaler(inner.marshaler)
