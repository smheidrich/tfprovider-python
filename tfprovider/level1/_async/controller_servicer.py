from sys import stderr
from typing import Any

from .. import grpc_controller_pb2, grpc_controller_pb2_grpc
from ..daemon_task import AsyncDaemonTask
from ..grpc_server import AsyncServer


class AsyncControllerServicer(grpc_controller_pb2_grpc.GRPCControllerServicer):
    def __init__(self, server: AsyncServer) -> None:
        self.server = server

    async def _stop_server(self) -> None:
        print(
            "stopping gRPC server after controller shutdown request",
            file=stderr,
        )
        await self.server.stop(2)

    async def Shutdown(
        self, request: Any, context: Any
    ) -> grpc_controller_pb2.Empty:
        # stopping the server is done in a separate task so we can finish
        # this call (there is a grace period for unfinished calls)
        self._stop_task = AsyncDaemonTask(self._stop_server)
        return grpc_controller_pb2.Empty()
