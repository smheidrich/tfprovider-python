from . import tfplugin64_pb2, tfplugin64_pb2_grpc


class ProviderServicer(tfplugin64_pb2_grpc.ProviderServicer):
    def GetMetadata(self, request, context):
        return tfplugin64_pb2.GetMetadata.Response(
            server_capabilities=tfplugin64_pb2.ServerCapabilities(
                # TODO make configurable
                plan_destroy=False,
                get_provider_schema_optional=False,
            ),
        )

    def GetProviderSchema(self, request, context):
        return tfplugin64_pb2.GetProviderSchema.Response(
            provider=tfplugin64_pb2.Schema(
                version=1,
                block=tfplugin64_pb2.Schema.Block(
                    version=1,
                    description="Hello World provider",
                    description_kind=tfplugin64_pb2.StringKind.PLAIN,
                ),
            ),
        )
