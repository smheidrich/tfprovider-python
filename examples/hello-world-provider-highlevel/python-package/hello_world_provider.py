from dataclasses import dataclass
from sys import stderr

from tfprovider.dynamic_value import DynamicValueDecoder
from tfprovider.rpc_plugin import RPCPluginServer
from tfprovider.tfplugin64_pb2 import (
    ConfigureProvider,
    GetMetadata,
    PlanResourceChange,
    ServerCapabilities,
    ValidateProviderConfig,
    ValidateResourceConfig,
)
from tfprovider.tfplugin64_pb2_grpc import ProviderServicer as BaseProviderServicer
from tfprovider.usable_schema import (
    Attribute,
    Block,
    ProviderSchema,
    Schema,
    StringKind,
)
from tfprovider.wire_format import ImmutableMsgPackish, StringWireType

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

@dataclass
class HelloWorldResConfig:
    foo: str

class HelloWorldResSchemaBlockDecoder(DynamicValueDecoder):
    def unmarshal(self, value: ImmutableMsgPackish) -> HelloWorldResConfig:
        assert isinstance(value, dict)
        return HelloWorldResConfig(foo=value["foo"])

class ProviderServicer(BaseProviderServicer):
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
        decoder = HelloWorldResSchemaBlockDecoder()
        config = decoder.decode(request.config)
        foo = config.foo
        print(f"{foo=}", file=stderr)
        return ValidateProviderConfig.Response()

    def ValidateResourceConfig(self, request, context):
        return ValidateResourceConfig.Response()

    def ConfigureProvider(self, request, context):
        return ConfigureProvider.Response()

    def PlanResourceChange(self, request, context):
        return PlanResourceChange.Response(planned_state=request.proposed_new_state)


def main():
    s = RPCPluginServer(ProviderServicer())
    s.run()


if __name__ == "__main__":
    main()
