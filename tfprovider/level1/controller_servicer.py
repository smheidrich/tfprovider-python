import asyncio
from sys import stderr
from threading import Thread

from . import grpc_controller_pb2, grpc_controller_pb2_grpc


class ControllerServicer(grpc_controller_pb2_grpc.GRPCControllerServicer):
    def __init__(self, server):
        self.server = server
        self.stop_thread = Thread(target=self._stop_server, daemon=True)

    def _stop_server(self):
        print(
            "stopping gRPC server after controller shutdown request",
            file=stderr,
        )
        self.server.stop(2)

    def Shutdown(self, request, context):
        # stopping the server is done in a separate thread so we can finish
        # this call (there is a grace period for unfinished calls)
        self.stop_thread.start()
        return grpc_controller_pb2.Empty()


class AsyncControllerServicer(grpc_controller_pb2_grpc.GRPCControllerServicer):
    def __init__(self, server):
        self.server = server

    async def _stop_server(self):
        print(
            "stopping gRPC server after controller shutdown request",
            file=stderr,
        )
        await self.server.stop(2)

    async def Shutdown(self, request, context):
        # stopping the server is done in a separate task so we can finish
        # this call (there is a grace period for unfinished calls)
        asyncio.create_task(self._stop_server())
        return grpc_controller_pb2.Empty()
