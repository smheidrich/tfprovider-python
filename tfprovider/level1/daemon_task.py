import asyncio
from collections.abc import Callable
from threading import Thread
from typing import Any


class AsyncDaemonTask:
    def __init__(self, coro_func: Callable[..., Any], /) -> None:
        asyncio.create_task(coro_func())


class SyncDaemonTask:
    def __init__(self, func: Callable[..., Any], /) -> None:
        t = Thread(target=func, daemon=True)
        t.start()
