from collections.abc import Generator
from contextlib import contextmanager
from traceback import format_exc

from ..level2.diagnostics import Diagnostics


@contextmanager
def exception_to_diagnostics(
    diagnostics: Diagnostics,
    action: str | None = None,
) -> Generator[None, None, None]:
    try:
        yield
    except Exception as e:
        summary = (
            f"error while {action}: {e}" if action is not None else str(e)
        )
        diagnostics.add_error(summary=summary, detail=format_exc())
