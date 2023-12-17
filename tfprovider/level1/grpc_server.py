"""
This serves only as a way for async source + auto-generated sync to get their
corresponding server type. Relies on name-based Async -> Sync replacement
feature of unasync.
"""
import grpc
import grpc.aio

AsyncServer = grpc.aio.Server
SyncServer= grpc.Server

__all__ = ["AsyncServer", "SyncServer"]
