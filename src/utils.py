"""
utils.py — Cross-cutting concerns: logging, decorators, timing.
"""

import time
import logging
import functools
from typing import Callable, TypeVar, Any

F = TypeVar("F", bound=Callable[..., Any])

# ──────────────────────────────────────────────
# Logger
# ──────────────────────────────────────────────

def setup_logger(name: str = "doc_gen", verbose: bool = False) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # avoid duplicate handlers on re-import

    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setLevel(level)
    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    return logger


logger = setup_logger()


# ──────────────────────────────────────────────
# Decorators
# ──────────────────────────────────────────────

def timer(fn: F) -> F:
    """Decorator: logs execution time of a function."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = fn(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.debug(f"⏱  {fn.__qualname__} → {elapsed:.2f}s")
        return result
    return wrapper  # type: ignore


def log_step(label: str) -> Callable[[F], F]:
    """Decorator factory: wraps a function with step start/end log lines."""
    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            logger.info(f"▶  {label}…")
            result = fn(*args, **kwargs)
            logger.info(f"✔  {label} — done")
            return result
        return wrapper  # type: ignore
    return decorator


# ──────────────────────────────────────────────
# Progress helper
# ──────────────────────────────────────────────

class ProgressBar:
    """
    Lightweight terminal progress bar — no external deps.

    Usage:
        bar = ProgressBar(total=10, label="Processing")
        for item in items:
            process(item)
            bar.step()
        bar.done()
    """

    def __init__(self, total: int, label: str = "Progress", width: int = 30) -> None:
        self.total = max(total, 1)
        self.label = label
        self.width = width
        self._current = 0
        self._render()

    def step(self, n: int = 1) -> None:
        self._current = min(self._current + n, self.total)
        self._render()

    def done(self) -> None:
        self._current = self.total
        self._render()
        print()  # final newline

    def _render(self) -> None:
        pct = self._current / self.total
        filled = int(self.width * pct)
        bar = "█" * filled + "░" * (self.width - filled)
        print(
            f"\r  [{bar}] {self._current:>{len(str(self.total))}}/{self.total} {self.label}",
            end="",
            flush=True,
        )
