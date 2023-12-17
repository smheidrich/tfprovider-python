"""
Schema definitions modeled after the protobuf ones, but more usable.

Specifically, this means that they contain high-level representations of type
fields instead of their byte representations.
"""
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import StrEnum, auto
from typing import Any, Generic, TypeVar, Union

from tfplugin_proto import tfplugin6_4_pb2 as pb

from .wire_format import AttributeWireType


class NotSet(StrEnum):
    NOT_SET = auto()


NOT_SET = NotSet.NOT_SET


@dataclass
class ProviderSchema:
    provider: Union["Schema", NotSet] = NOT_SET
    resource_schemas: Mapping[str, "Schema"] | NotSet = NOT_SET

    def to_protobuf(self) -> pb.GetProviderSchema.Response:
        d: dict[str, Any] = {}
        if self.provider != NOT_SET:
            d["provider"] = self.provider.to_protobuf()
        # Mypy like this better than != NOT_SET:
        if not isinstance(self.resource_schemas, NotSet):
            d["resource_schemas"] = {
                k: v.to_protobuf() for k, v in self.resource_schemas.items()
            }
        return pb.GetProviderSchema.Response(**d)


@dataclass
class Schema:
    version: int | NotSet = NOT_SET
    block: Union["Block", NotSet] = NOT_SET

    def to_protobuf(self) -> pb.Schema:
        d = {k: v for k, v in asdict(self).items() if v != NOT_SET}
        if self.block != NOT_SET:
            d["block"] = self.block.to_protobuf()
        return pb.Schema(**d)


@dataclass
class Block:
    version: int | NotSet = NOT_SET
    attributes: list["Attribute[Any]"] | NotSet = NOT_SET
    # block_types  # TODO
    description: str | NotSet = NOT_SET
    description_kind: Union["StringKind", NotSet] = NOT_SET
    deprecated: bool | NotSet = NOT_SET

    def to_protobuf(self) -> pb.Schema.Block:
        d = {k: v for k, v in asdict(self).items() if v != NOT_SET}
        if self.attributes != NOT_SET:
            d["attributes"] = [a.to_protobuf() for a in self.attributes]
        if self.description_kind != NOT_SET:
            d["description_kind"] = self.description_kind.to_protobuf()
        return pb.Schema.Block(**d)


W = TypeVar("W", bound=AttributeWireType[Any])


@dataclass
class Attribute(Generic[W]):
    name: str
    type: W
    # nested_type: NestingObject  # TODO
    description: str | NotSet = NOT_SET
    required: bool | NotSet = NOT_SET
    optional: bool | NotSet = NOT_SET
    computed: bool | NotSet = NOT_SET
    sensitive: bool | NotSet = NOT_SET
    description_kind: Union["StringKind", NotSet] = NOT_SET
    deprecated: bool | NotSet = NOT_SET

    def to_protobuf(self) -> pb.Schema.Attribute:
        d = {k: v for k, v in asdict(self).items() if v != NOT_SET}
        d["type"] = self.type.serialize_type()
        if self.description_kind != NOT_SET:
            d["description_kind"] = self.description_kind.to_protobuf()
        return pb.Schema.Attribute(**d)


class StringKind(StrEnum):
    PLAIN = auto()
    MARKDOWN = auto()

    def to_protobuf(self) -> pb.StringKind:
        return {
            StringKind.PLAIN: pb.StringKind.PLAIN,
            StringKind.MARKDOWN: pb.StringKind.MARKDOWN,
        }[self]
