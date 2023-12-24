"""
Helpers for working with schemas that can be statically type checked.
"""

import json
from collections.abc import Callable
from dataclasses import Field, dataclass, field, fields
from inspect import get_annotations
from typing import Any, TypeVar, Union, cast, dataclass_transform

from tfplugin_proto import tfplugin6_4_pb2 as pb

from ..level2.dynamic_value import (
    deserialize_dynamic_value,
    serialize_to_dynamic_value,
)
from ..level2.usable_schema import (
    NOT_SET,
    Attribute,
    NotSet,
    ProviderSchema,
    StringKind,
)
from ..level2.wire_format import (
    AttributeWireType,
    ImmutableMsgPackish,
    OptionalWireType,
    SetWireType,
    StringWireType,
    Unknown,
)
from ..level2.wire_marshaling import (
    AttributeWireTypeMarshaler,
    AttributeWireTypeUnmarshaler,
)
from ..level2.wire_representation import (
    MaybeUnknownWireRepresentation,
    OptionalWireRepresentation,
    SetWireRepresentation,
    StringWireRepresentation,
    WireRepresentation,
)

T = TypeVar("T")
M = TypeVar("M", bound=ImmutableMsgPackish)
W = TypeVar("W", bound=AttributeWireType[Any])


def attribute(
    # dataclasses
    *args: Any,
    # Terraform
    description: str | NotSet = NOT_SET,
    required: bool | NotSet = NOT_SET,
    optional: bool | NotSet = NOT_SET,
    computed: bool | NotSet = NOT_SET,
    sensitive: bool | NotSet = NOT_SET,
    description_kind: Union["StringKind", NotSet] = NOT_SET,
    deprecated: bool | NotSet = NOT_SET,
    # tfprovider
    representation: WireRepresentation[M, T] | None = None,
    wire_type: AttributeWireType[M] | None = None,
    marshaler: AttributeWireTypeMarshaler[AttributeWireType[M], T]
    | None = None,
    unmarshaler: AttributeWireTypeUnmarshaler[AttributeWireType[M], T]
    | None = None,
    # dataclasses
    **kwargs: Any,
) -> Any:
    """
    Customize a Terraform schema attribute.

    Analogue of `dataclasses.field`.
    """
    return field(
        *args,
        metadata={
            "terraform": {
                "description": description,
                "required": required,
                "optional": optional,
                "computed": computed,
                "sensitive": sensitive,
                "description_kind": description_kind,
                "deprecated": deprecated,
            },
            "tfprovider": {
                "representation": representation,
                "wire_type": wire_type,
                "marshaler": marshaler,
                "unmarshaler": unmarshaler,
            },
        },
        **kwargs,
    )


@dataclass_transform(field_specifiers=(attribute, Field))
def attributes_class(
    *args: Any, **kwargs: Any
) -> Callable[[type[T]], type[T]]:
    """
    Mark a class as representing a Terraform schema attribute list type.

    Transforms the class in much the same way as `dataclasses.dataclass` does,
    generating an appropriate constructor.

    The specifics of how to map attribute types and values to Terraform's wire
    format can be customized using `attribute`.
    """

    def _schema(klass: type[T]) -> type[T]:
        return cast(type[T], dataclass(*args, **kwargs)(klass))

    return _schema


ANNOTATION_TO_REPRESENTATION: dict[Any, WireRepresentation[Any, Any]] = {
    str: StringWireRepresentation(),
    # TODO make this happen automatically
    (str | None): OptionalWireRepresentation(StringWireRepresentation()),
    (str | Unknown): MaybeUnknownWireRepresentation(
        StringWireRepresentation()
    ),
    (str | None | Unknown): MaybeUnknownWireRepresentation(
        OptionalWireRepresentation(StringWireRepresentation())
    ),
    set[str]: SetWireRepresentation(StringWireRepresentation()),
    (set[str] | None): OptionalWireRepresentation(
        SetWireRepresentation(StringWireRepresentation())
    ),
    (set[str] | None | Unknown): MaybeUnknownWireRepresentation(
        OptionalWireRepresentation(
            SetWireRepresentation(StringWireRepresentation())
        )
    ),
    (set[str | Unknown] | None): OptionalWireRepresentation(
        SetWireRepresentation(
            MaybeUnknownWireRepresentation(StringWireRepresentation())
        )
    ),
}

ANNOTATION_TO_WIRE_TYPE: dict[Any, AttributeWireType[Any]] = {
    str: StringWireType(),
    # TODO make this happen automatically
    (str | None): StringWireType(),
    (str | Unknown): StringWireType(),
    (str | None | Unknown): StringWireType(),
    set[str]: SetWireType(StringWireType()),
    (set[str] | None): OptionalWireType(SetWireType(StringWireType())),
    (set[str] | None | Unknown): OptionalWireType(
        SetWireType(StringWireType())
    ),
    (set[str | Unknown] | None): OptionalWireType(
        SetWireType(StringWireType())
    ),
}


def attributes_class_to_usable(klass: type) -> list[Attribute[Any]]:
    """
    Transform an `@attribute_class`-decorated class to its usable schema repr.

    "Usable" schemas are thin wrappers around Terraform's own Protobuf schema
    classes, the only difference between the two being that types are
    represented as `WireType` instances in the former and serialized `bytes` in
    the latter.

    You don't normally have to use this function unless you're trying to do
    something strange. `attributes_class_to_protobuf` is the one you'll
    usually want, to go directly to Terraform's representation.
    """
    annotations = get_annotations(klass)
    return [
        Attribute(
            name=f.name,
            type=(
                wt
                if (
                    wt := f.metadata["tfprovider"].get("wire_type") is not None
                )
                else rep.attribute_wire_type
                if (rep := f.metadata["tfprovider"].get("representation"))
                is not None
                else ANNOTATION_TO_WIRE_TYPE[annotations[f.name]]
            ),
            **f.metadata["terraform"],
        )
        for f in fields(klass)
    ]


def attributes_class_to_protobuf(klass: type) -> list[pb.Schema.Attribute]:
    """
    Transform an `@attribute_class`-decorated class to Terraform Protobuf.
    """
    return [a.to_protobuf() for a in attributes_class_to_usable(klass)]


def deserialize_dynamic_value_into_attribute_class_instance(
    value: pb.DynamicValue, klass: type[T]
) -> T:
    marshaled_value = deserialize_dynamic_value(value)
    return unmarshal_msgpack_into_attributes_class_instance(
        marshaled_value, klass
    )


def deserialize_dynamic_value_into_optional_attribute_class_instance(
    value: pb.DynamicValue, klass: type[T]
) -> T | None:
    marshaled_value = deserialize_dynamic_value(value)
    if marshaled_value is None:
        return None
    return unmarshal_msgpack_into_attributes_class_instance(
        marshaled_value, klass
    )


def deserialize_raw_state_into_optional_attribute_class_instance(
    value: pb.RawState, klass: type[T]
) -> T | None:
    # TODO handle flatmap
    marshaled_value = json.loads(value.json)  # TODO use/introd. l2 func?
    if marshaled_value is None:
        return None
    return unmarshal_msgpack_into_attributes_class_instance(
        marshaled_value, klass
    )


def serialize_attribute_class_instance_to_dynamic_value(
    instance: T,
) -> pb.DynamicValue:
    marshaled_value = marshal_attributes_class_instance_to_msgpack(instance)
    return serialize_to_dynamic_value(marshaled_value)


def serialize_optional_attribute_class_instance_to_dynamic_value(
    instance: T | None,
) -> pb.DynamicValue:
    marshaled_value = (
        marshal_attributes_class_instance_to_msgpack(instance)
        if instance is not None
        else None
    )
    return serialize_to_dynamic_value(marshaled_value)


# TODO what about json?
def unmarshal_msgpack_into_attributes_class_instance(
    marshaled_dict: ImmutableMsgPackish, klass: type[T]
) -> T:
    if not isinstance(marshaled_dict, dict):
        raise TypeError(
            f"Expected dict but got {type(marshaled_dict).__name__} "
            f"{marshaled_dict!r}"
        )
    annotations = get_annotations(klass)
    constructor_kwargs = {}
    # TODO see https://github.com/python/mypy/issues/14941 for why
    #   dataclass+type[T] doesn't currently work => typing disabled for now:
    for attr_field in fields(klass):  # type: ignore
        try:
            name = attr_field.name
            marshaled_value = marshaled_dict[name]  # TODO error handling
            config = attr_field.metadata["tfprovider"]
            if (representation := config.get("representation")) is not None:
                unmarshaled_value = representation.unmarshal_value_msgpack(
                    marshaled_value
                )
            elif (unmarshaler := config.get("unmarshaler")) is not None:
                unmarshaled_value = unmarshaler.unmarshal_msgpack(
                    marshaled_value
                )
            else:
                annotation = annotations[name]
                representation = ANNOTATION_TO_REPRESENTATION[annotation]
                unmarshaled_value = representation.unmarshal_value_msgpack(
                    marshaled_value
                )
            constructor_kwargs[name] = unmarshaled_value
        except Exception as e:
            # TODO better exception type
            raise ValueError(
                f"error unmarshaling attribute {attr_field.name!r}"
            ) from e
    return klass(**constructor_kwargs)


def marshal_attributes_class_instance_to_msgpack(
    instance: T,
) -> ImmutableMsgPackish:
    annotations = get_annotations(instance.__class__)
    result_dict = {}
    for attr_field in fields(instance):  # type: ignore
        name = attr_field.name
        unmarshaled_value = getattr(instance, name)  # TODO error handling
        config = attr_field.metadata["tfprovider"]
        if (representation := config.get("representation")) is not None:
            marshaled_value = representation.marshal_value_msgpack(
                unmarshaled_value
            )
        elif (marshaler := config.get("marshaler")) is not None:
            marshaled_value = marshaler.unmarshal_msgpack(unmarshaled_value)
        else:
            annotation = annotations[name]
            representation = ANNOTATION_TO_REPRESENTATION[annotation]
            marshaled_value = representation.marshal_value_msgpack(
                unmarshaled_value
            )
        result_dict[name] = marshaled_value
    return result_dict


# TODO later:


def to_usable_provider_schema(schema: type[T]) -> ProviderSchema:
    """
    Transform a schema to a "usable" provider schema.

    "Usable" schemas are thin wrappers around Terraform's own Protobuf schema
    classes, the only difference between the two being that types are
    represented as `WireType` instances in the former and serialized `bytes` in
    the latter.

    You don't normally have to use this function unless you're trying to do
    something strange.
    """
    raise NotImplementedError("")


def to_protobuf_schema(schema: type[T]) -> pb.GetProviderSchema.Response:
    """
    Transform a schema to a Terraform Protobuf provider schema.
    """
    raise NotImplementedError("")
