import threading
from concurrent import futures
from time import sleep

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc


def _toggle_health(
    health_servicer: health.HealthServicer, service: str
) -> None:
    next_status = health_pb2.HealthCheckResponse.SERVING
    while True:
        health_servicer.set(service, next_status)
        sleep(5)


def _configure_health_server(server: grpc.Server) -> None:
    health_servicer = health.HealthServicer(
        experimental_non_blocking=True,
        experimental_thread_pool=futures.ThreadPoolExecutor(max_workers=10),
    )
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)

    # Use a daemon thread to toggle health status
    toggle_health_status_thread = threading.Thread(
        target=_toggle_health,
        args=(health_servicer, "helloworld.Greeter"),
        daemon=True,
    )
    toggle_health_status_thread.start()
