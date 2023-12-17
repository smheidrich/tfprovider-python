import os
from sys import stderr

from .._common.rpc_plugin_server import (
    RPCPluginServerBase,
    print_handshake_response,
)
from ..controller_servicer import AsyncControllerServicer
from ..grpc_server_factory import AsyncServerFactory


class AsyncRPCPluginServer(RPCPluginServerBase):
    _server_factory = AsyncServerFactory
    _controller_servicer_factory = AsyncControllerServicer

    async def run(self) -> None:
        parent_pid = os.getppid()
        await self.server.start()
        print(f"server listening on port {self.port}", file=stderr)
        print_handshake_response(self.port, self.cert_base64)
        # RPCPlugin clients stop plugins with SIGKILL, which kills a process
        # immediately but leaves its children intact. Python RPCPlugin servers
        # will generally be launched by a bash script, so SIGKILL will only
        # kill that script's process but not the Python interpreter. A simple
        # way to detect this is to see if the parent PID has changed:
        while os.getppid() == parent_pid:
            if not await self.server.wait_for_termination(1):
                break
