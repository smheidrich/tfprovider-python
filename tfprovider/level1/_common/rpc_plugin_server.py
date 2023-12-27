from hc_go_plugin_server._common.rpc_plugin_server import (
    RPCPluginServerBase as ExtRPCPluginServerBase,
)
from tfplugin_proto import tfplugin6_4_pb2_grpc


class RPCPluginServerBase(ExtRPCPluginServerBase):
    def __init__(
        self,
        provider_servicer: tfplugin6_4_pb2_grpc.ProviderServicer,
        port: str = "0",
    ):
        super().__init__(port=port)
        tfplugin6_4_pb2_grpc.add_ProviderServicer_to_server(  # type: ignore
            provider_servicer, self.server
        )
