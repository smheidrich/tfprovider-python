from tfprovider.rpc_plugin import RPCPluginServer
from tfprovider.tfplugin64_pb2 import (
    GetMetadata,
    GetProviderSchema,
    Schema,
    ServerCapabilities,
    StringKind,
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
                ),
            ),
        )


def main():
    s = RPCPluginServer(ProviderServicer())
    s.run()


if __name__ == "__main__":
    main()
