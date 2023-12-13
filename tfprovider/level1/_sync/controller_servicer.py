from sys import stderr

from ..daemon_task import SyncDaemonTask
from .. import grpc_controller_pb2, grpc_controller_pb2_grpc


class SyncControllerServicer(grpc_controller_pb2_grpc.GRPCControllerServicer):
    def __init__(self, server):
        self.server = server

    def _stop_server(self):
        print(
            "stopping gRPC server after controller shutdown request",
            file=stderr,
        )
        self.server.stop(2)

    def Shutdown(self, request, context):
        # stopping the server is done in a separate task so we can finish
        # this call (there is a grace period for unfinished calls)
        self._stop_task = SyncDaemonTask(self._stop_server)
        return grpc_controller_pb2.Empty()
