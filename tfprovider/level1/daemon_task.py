import asyncio
from threading import Thread


class AsyncDaemonTask:
    def __init__(self, coro_func, /) -> None:
        asyncio.create_task(coro_func())


class SyncDaemonTask:
    def __init__(self, func, /) -> None:
        t = Thread(target=func, daemon=True)
        t.start()
