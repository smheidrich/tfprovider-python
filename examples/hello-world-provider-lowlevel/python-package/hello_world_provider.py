from tfprovider.rpc_plugin import RPCPluginServer
from tfprovider.tfplugin64_pb2 import (
    GetMetadata,
    GetProviderSchema,
    Schema,
    ServerCapabilities,
    StringKind,
    ValidateProviderConfig,
    ValidateResourceConfig,
)
from tfprovider.tfplugin64_pb2_grpc import ProviderServicer


class ProviderServicer(ProviderServicer):
    def GetMetadata(self, request, context):
        return GetMetadata.Response(
            server_capabilities=ServerCapabilities(
                plan_destroy=False, get_provider_schema_optional=False
            ),
        )

    def GetProviderSchema(self, request, context):
        return GetProviderSchema.Response(
            provider=Schema(
                version=1,
                block=Schema.Block(
                    version=1,
                    description="Hello World provider",
                    description_kind=StringKind.PLAIN,
                    attributes=[
                        Schema.Attribute(
                            name="foo",
                            type=b'"string"',
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
                    block=Schema.Block(
                        version=1,
                        description="Some resource",
                        description_kind=StringKind.PLAIN,
                        attributes=[
                            Schema.Attribute(
                                name="foo",
                                type=b'"string"',
                                required=True,
                                description="Some attribute in the resource",
                            )
                        ],
                    ),
                )
            },
        )

    def ValidateProviderConfig(self, request, context):
        return ValidateProviderConfig.Response()

    def ValidateResourceConfig(self, request, context):
        return ValidateResourceConfig.Response()


def main():
    s = RPCPluginServer(ProviderServicer())
    s.run()


if __name__ == "__main__":
    main()
