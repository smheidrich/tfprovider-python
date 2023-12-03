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
)


@dataclass
class WireRepresentation(ABC):
    attribute_wire_type: AttributeWireType
    unmarshaler: AttributeWireTypeUnmarshaler

    @abstractmethod
    def unmarshal_value_msgpack(self, value: ImmutableMsgPackish) -> str:
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

    def unmarshal_value_msgpack(self, value: ImmutableMsgPackish) -> str:
        return self.unmarshaler.unmarshal_msgpack(value)
