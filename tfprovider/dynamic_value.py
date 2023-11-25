import json
from collections.abc import Mapping
from typing import Any, TypeVar

import msgpack

from tfprovider.tfplugin64_pb2 import DynamicValue

from .usable_schema import NOT_SET, Attribute, Block
from .wire_format import (
    ImmutableMsgPackish,
    JsonAndMsgpackSerializableWireType,
)

F = TypeVar("F")
T = TypeVar("T")


def decode_dynamic_value(
    value: DynamicValue, wire_type: JsonAndMsgpackSerializableWireType[F, T]
) -> T:
    # TODO let this use deserialize_dynamic_value below (=> DRY)? if we keep it
    #   at all, that is
    if (b := value.msgpack) is not None:
        msgpackish = msgpack.unpackb(b)
        return wire_type.unmarshal_value_msgpack(msgpackish)
    elif (b := value.json) is not None:
        jsonish = json.loads(b.decode("utf-8"))
        return wire_type.unmarshal_value_json(jsonish)
    else:
        raise ValueError(
            f"can't decode DynamicValue {value!r} which is neither JSON nor msgpack"
        )


def encode_dynamic_value_msgpack(
    value: F, wire_type: JsonAndMsgpackSerializableWireType[F, T]
) -> DynamicValue:
    msgpackish = wire_type.marshal_value_msgpack(value)
    return DynamicValue(msgpack=msgpack.packb(msgpackish), json=None)


def deserialize_dynamic_value(value: DynamicValue) -> ImmutableMsgPackish:
    if (b := value.msgpack) is not None:
        return msgpack.unpackb(b)
    elif (b := value.json) is not None:
        return json.loads(b.decode("utf-8"))


# TODO find a cleverer solution to this, e.g. ABC for a decoder that decodes to
#   a user-defined type, which users have to implement


def decode_block_dynamic_value(
    value: DynamicValue, block_schema: Block
) -> dict[str, Any]:
    msgpackish = deserialize_dynamic_value(value)
    if not isinstance(msgpackish, Mapping):
        raise TypeError(
            "when decoding Block DynamicValue, expected serialized value to "
            f"be a mapping, but got {type(msgpackish)} instead"
        )
    attr_schemas: list[Attribute] = (
        block_schema.attributes
        if block_schema.attributes and block_schema.attributes != NOT_SET
        else []
    )
    result = {}
    for attr_schema in attr_schemas:
        attr_name = attr_schema.name
        if attr_name not in msgpackish:
            continue
        result[attr_name] = attr_schema.type.unmarshal_value_msgpack(
            msgpackish[attr_name]
        )
    return result
