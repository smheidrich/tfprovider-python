"""
Helpers for working with schemas that can be statically type checked.
"""

from collections.abc import Callable
from dataclasses import Field, dataclass, field, fields
from inspect import get_annotations
from typing import Any, TypeVar, Union, dataclass_transform

from tfprovider.wire_format import StringWireType

from . import tfplugin64_pb2 as pb
from .usable_schema import (
    NOT_SET,
    Attribute,
    NotSet,
    ProviderSchema,
    StringKind,
)

T = TypeVar("T")


def attribute(
    # dataclasses
    *args,
    # Terraform
    description: str | NotSet = NOT_SET,
    required: bool | NotSet = NOT_SET,
    optional: bool | NotSet = NOT_SET,
    computed: bool | NotSet = NOT_SET,
    sensitive: bool | NotSet = NOT_SET,
    description_kind: Union["StringKind", NotSet] = NOT_SET,
    deprecated: bool | NotSet = NOT_SET,
    # tfprovider
    representation=None,
    wire_type=None,
    marshaler=None,
    unmarshaler=None,
    # dataclasses
    **kwargs,
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
def attributes_class(*args, **kwargs) -> Callable[[type[T]], type[T]]:
    """
    Mark a class as representing a Terraform schema attribute list type.

    Transforms the class in much the same way as `dataclasses.dataclass` does,
    generating an appropriate constructor.

    The specifics of how to map attribute types and values to Terraform's wire
    format can be customized using `attribute`.
    """

    def _schema(klass: type[T]) -> type[T]:
        return dataclass(*args, **kwargs)(klass)

    return _schema


ANNOTATION_TO_WIRE_TYPE = {
    str: StringWireType(),
}


def attributes_class_to_usable(klass) -> list[Attribute]:
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
                else ANNOTATION_TO_WIRE_TYPE[annotations[f.name]]
            ),
            **f.metadata["terraform"],
        )
        for f in fields(klass)
    ]


def attributes_class_to_protobuf(klass) -> list[pb.Schema.Attribute]:
    """
    Transform an `@attribute_class`-decorated class to Terraform Protobuf.
    """
    return [a.to_protobuf() for a in attributes_class_to_usable(klass)]


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
