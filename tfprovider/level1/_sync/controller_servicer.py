from sys import stderr
from typing import Any

from .. import grpc_controller_pb2, grpc_controller_pb2_grpc
from ..daemon_task import SyncDaemonTask
from ..grpc_server import SyncServer


class SyncControllerServicer(grpc_controller_pb2_grpc.GRPCControllerServicer):
    def __init__(self, server: SyncServer) -> None:
        self.server = server

    def _stop_server(self) -> None:
        print(
            "stopping gRPC server after controller shutdown request",
            file=stderr,
        )
        self.server.stop(2)

    def Shutdown(
        self, request: Any, context: Any
    ) -> grpc_controller_pb2.Empty:
        # stopping the server is done in a separate task so we can finish
        # this call (there is a grace period for unfinished calls)
        self._stop_task = SyncDaemonTask(self._stop_server)
        return grpc_controller_pb2.Empty()
