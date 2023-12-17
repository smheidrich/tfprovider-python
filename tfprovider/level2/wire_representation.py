"""
Combined wire type + value marshaling/unmarshaling.
"""
# TODO better name might be type mapping? or sth. like that.

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from .wire_format import (
    AttributeWireType,
    ImmutableJsonishWithUnknown,
    ImmutableMsgPackish,
    OptionalWireType,
    StringWireType,
)
from .wire_marshaling import (
    AttributeWireTypeMarshaler,
    AttributeWireTypeUnmarshaler,
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
    unmarshaler: AttributeWireTypeUnmarshaler[AttributeWireType[M]]
    marshaler: AttributeWireTypeMarshaler[AttributeWireType[M]]

    @abstractmethod
    def unmarshal_value_msgpack(
        self, value: ImmutableMsgPackish
    ) -> ImmutableJsonishWithUnknown:
        pass

    @abstractmethod
    def marshal_value_msgpack(self, value: ImmutableJsonishWithUnknown) -> M:
        pass


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

    def unmarshal_value_msgpack(self, value: ImmutableMsgPackish) -> str:
        return self.unmarshaler.unmarshal_msgpack(value)

    def marshal_value_msgpack(self, value: ImmutableJsonishWithUnknown) -> str:
        return self.marshaler.marshal_msgpack(value)


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

    # TODO DRY? see above

    def unmarshal_value_msgpack(
        self, value: ImmutableMsgPackish
    ) -> ImmutableJsonishWithUnknown:
        return self.unmarshaler.unmarshal_msgpack(value)

    def marshal_value_msgpack(
        self, value: ImmutableJsonishWithUnknown
    ) -> M | None:
        return self.marshaler.marshal_msgpack(value)
