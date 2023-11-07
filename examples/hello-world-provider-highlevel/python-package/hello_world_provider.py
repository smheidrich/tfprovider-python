import json
from sys import stderr

import msgpack

from tfprovider.rpc_plugin import RPCPluginServer
from tfprovider.tfplugin64_pb2 import (
    GetMetadata,
    ServerCapabilities,
    ValidateProviderConfig,
    ValidateResourceConfig,
)
from tfprovider.tfplugin64_pb2_grpc import ProviderServicer
from tfprovider.usable_schema import (
    Attribute,
    Block,
    ProviderSchema,
    Schema,
    StringKind,
)
from tfprovider.wire_format import StringWireType

provider_schema = ProviderSchema(
    provider=Schema(
        version=1,
        block=Block(
            version=1,
            attributes=[
                Attribute(
                    name="foo",
                    type=StringWireType(),
                    description="Some attribute",
                    # has no effect here for some reason...
                    required=True,
                )
            ],
        ),
    ),
    resource_schemas={
        "helloworld_res": Schema(
            version=1,
            block=Block(
                version=1,
                description="Some resource",
                description_kind=StringKind.PLAIN,
                attributes=[
                    Attribute(
                        name="foo",
                        type=StringWireType(),
                        description="Some attribute in the resource",
                        required=True,
                    )
                ],
            ),
        )
    },
)


class ProviderServicer(ProviderServicer):
    def GetMetadata(self, request, context):
        return GetMetadata.Response(
            server_capabilities=ServerCapabilities(
                plan_destroy=False, get_provider_schema_optional=False
            ),
        )

    def GetProviderSchema(self, request, context):
        return provider_schema.to_protobuf()

    def ValidateProviderConfig(self, request, context):
        print(request.config, file=stderr)
        print(type(request.config.msgpack), file=stderr)
        if b := request.config.msgpack:
            block = msgpack.unpackb(b)
            foo = StringWireType().unmarshal_value_msgpack(block["foo"])
            print(f"{foo=}", file=stderr)
        elif b := request.config.json:
            block = json.loads(b.decode("utf-8"))
            foo = StringWireType().unmarshal_value_json(block["foo"])
            print(f"{foo=}", file=stderr)
        return ValidateProviderConfig.Response()

    def ValidateResourceConfig(self, request, context):
        return ValidateResourceConfig.Response()


def main():
    s = RPCPluginServer(ProviderServicer())
    s.run()


if __name__ == "__main__":
    main()
