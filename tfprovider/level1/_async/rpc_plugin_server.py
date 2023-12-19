from hc_go_plugin_server.rpc_plugin import (
    AsyncRPCPluginServer as ExtAsyncRPCPluginServer,
)

from .._common.rpc_plugin_server import RPCPluginServerBase


class AsyncRPCPluginServer(RPCPluginServerBase, ExtAsyncRPCPluginServer):
    pass
