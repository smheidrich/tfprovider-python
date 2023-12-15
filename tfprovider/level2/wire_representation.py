"""
Combined wire type + value marshaling/unmarshaling.
"""
# TODO better name might be type mapping? or sth. like that.

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .wire_format import (
    AttributeWireType,
    ImmutableJsonishWithUnknown,
    ImmutableMsgPackish,
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


@dataclass
class WireRepresentation(ABC):
    attribute_wire_type: AttributeWireType
    unmarshaler: AttributeWireTypeUnmarshaler
    marshaler: AttributeWireTypeMarshaler

    @abstractmethod
    def unmarshal_value_msgpack(
        self, value: ImmutableMsgPackish
    ) -> ImmutableJsonishWithUnknown:
        pass

    @abstractmethod
    def marshal_value_msgpack(
        self, value: ImmutableJsonishWithUnknown
    ) -> ImmutableMsgPackish:
        pass


@dataclass
class StringWireRepresentation(WireRepresentation):
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

    def marshal_value_msgpack(
        self, value: ImmutableJsonishWithUnknown
    ) -> ImmutableMsgPackish:
        return self.marshaler.marshal_msgpack(value)


@dataclass
class OptionalWireRepresentation(WireRepresentation):
    """
    Wrapper around another representation to make it allow null values.
    """

    inner: WireRepresentation
    attribute_wire_type: AttributeWireType
    unmarshaler: OptionalWireTypeUnmarshaler
    marshaler: OptionalWireTypeMarshaler

    def __init__(self, inner: WireRepresentation):
        self.inner = inner
        self.attribute_wire_type = inner.attribute_wire_type
        self.unmarshaler = OptionalWireTypeUnmarshaler(inner.unmarshaler)
        self.marshaler = OptionalWireTypeMarshaler(inner.marshaler)

    # TODO DRY? see above

    def unmarshal_value_msgpack(
        self, value: ImmutableMsgPackish
    ) -> ImmutableJsonishWithUnknown:
        return self.unmarshaler.unmarshal_msgpack(value)

    def marshal_value_msgpack(
        self, value: ImmutableJsonishWithUnknown
    ) -> ImmutableMsgPackish:
        return self.marshaler.marshal_msgpack(value)
