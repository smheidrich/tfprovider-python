from hc_go_plugin_server.rpc_plugin import (
    SyncRPCPluginServer as ExtAsyncRPCPluginServer,
)

from .._common.rpc_plugin_server import RPCPluginServerBase


class SyncRPCPluginServer(RPCPluginServerBase, ExtAsyncRPCPluginServer):
    pass
