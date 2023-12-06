"""
Combined wire type + value marshaling/unmarshaling.
"""
# TODO better name might be type mapping? or sth. like that.

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .wire_format import AttributeWireType, ImmutableMsgPackish, StringWireType
from .wire_marshaling import (
    AttributeWireTypeUnmarshaler,
    StringWireTypeUnmarshaler,
    StringWireTypeMarshaler,
)


@dataclass
class WireRepresentation(ABC):
    attribute_wire_type: AttributeWireType
    unmarshaler: AttributeWireTypeUnmarshaler

    @abstractmethod
    def unmarshal_value_msgpack(self, value: ImmutableMsgPackish) -> str:
        pass

    @abstractmethod
    def marshal_value_msgpack(self, value: str) -> ImmutableMsgPackish:
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

    def marshal_value_msgpack(self, value: str) -> ImmutableMsgPackish:
        return self.marshaler.marshal_msgpack(value)
