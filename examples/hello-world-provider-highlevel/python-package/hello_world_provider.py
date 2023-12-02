from sys import stderr

from tfprovider.dynamic_value import DynamicValueDecoder
from tfprovider.rpc_plugin import RPCPluginServer
from tfprovider.statically_typed_schema import (
    attribute,
    attributes_class,
    attributes_class_to_usable,
)
from tfprovider.tfplugin64_pb2 import (
    ConfigureProvider,
    GetMetadata,
    PlanResourceChange,
    ServerCapabilities,
    ValidateProviderConfig,
    ValidateResourceConfig,
)
from tfprovider.tfplugin64_pb2_grpc import ProviderServicer as BaseProviderServicer
from tfprovider.usable_schema import Block, ProviderSchema, Schema, StringKind
from tfprovider.wire_format import ImmutableMsgPackish
from tfprovider.wire_marshaling import StringWireTypeUnmarshaler


@attributes_class()
class HelloWorldCompleteProviderConfig:
    foo: str = attribute(required=True)


@attributes_class()
class HelloWorldCompleteResConfig:
    foo: str = attribute(required=True)
    # bar: datetime = attribute(representation=DateAsStringRepr())


provider_schema = ProviderSchema(
    provider=Schema(
        version=1,
        block=Block(
            version=1,
            attributes=attributes_class_to_usable(HelloWorldCompleteProviderConfig),
        ),
    ),
    resource_schemas={
        "helloworld_res": Schema(
            version=1,
            block=Block(
                version=1,
                description="Some resource",
                description_kind=StringKind.PLAIN,
                attributes=attributes_class_to_usable(HelloWorldCompleteResConfig),
            ),
        )
    },
)


class HelloWorldResSchemaBlockDecoder(DynamicValueDecoder):
    def unmarshal(self, value: ImmutableMsgPackish) -> HelloWorldCompleteResConfig:
        assert isinstance(value, dict)

        return HelloWorldCompleteResConfig(
            foo=StringWireTypeUnmarshaler().unmarshal_msgpack(value["foo"])
        )


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
