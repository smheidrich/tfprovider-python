"""
This serves only as a way for async source + auto-generated sync to get their
corresponding server factory variant. Relies on name-based Async -> Sync
replacement feature of unasync.
"""
import grpc
import grpc.aio

AsyncServerFactory = grpc.aio.server
SyncServerFactory= grpc.server

__all__ = ["AsyncServerFactory", "SyncServerFactory"]
