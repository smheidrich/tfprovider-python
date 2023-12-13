from ._async.rpc_plugin_server import AsyncRPCPluginServer
from ._sync.rpc_plugin_server import SyncRPCPluginServer

RPCPluginServer = SyncRPCPluginServer  # shortcut

__all__ = ["AsyncRPCPluginServer", "SyncRPCPluginServer", "RPCPluginServer"]
