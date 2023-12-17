import os
from sys import stderr

from .._common.rpc_plugin_server import (
    RPCPluginServerBase,
    print_handshake_response,
)
from ..controller_servicer import SyncControllerServicer
from ..grpc_server_factory import SyncServerFactory


class SyncRPCPluginServer(RPCPluginServerBase):
    _server_factory = SyncServerFactory
    _controller_servicer_factory = SyncControllerServicer

    def run(self) -> None:
        parent_pid = os.getppid()
        self.server.start()
        print(f"server listening on port {self.port}", file=stderr)
        print_handshake_response(self.port, self.cert_base64)
        # RPCPlugin clients stop plugins with SIGKILL, which kills a process
        # immediately but leaves its children intact. Python RPCPlugin servers
        # will generally be launched by a bash script, so SIGKILL will only
        # kill that script's process but not the Python interpreter. A simple
        # way to detect this is to see if the parent PID has changed:
        while os.getppid() == parent_pid:
            if not self.server.wait_for_termination(1):
                break
