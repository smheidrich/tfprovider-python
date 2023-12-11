from collections.abc import Generator
from contextlib import contextmanager
from traceback import format_exc

from ..level2.diagnostics import Diagnostics


@contextmanager
def exception_to_diagnostics(
    diagnostics: Diagnostics,
) -> Generator[None, None, None]:
    try:
        yield
    except Exception as e:
        diagnostics.add_error(summary=str(e), detail=format_exc())
