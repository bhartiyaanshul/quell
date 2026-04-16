"""Loguru-based structured logger for Quell.

Call `setup_logger()` once at process startup to configure the global logger.
Import `logger` directly from `loguru` in all other modules.
"""

from __future__ import annotations

import sys

from loguru import logger


def setup_logger(level: str = "INFO", json: bool = False) -> None:
    """Configure the global Loguru logger.

    Args:
        level: Minimum log level to emit (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json: If True, emit structured JSON lines instead of human-readable output.
    """
    logger.remove()

    if json:
        logger.add(sys.stderr, serialize=True, level=level, enqueue=True)
    else:
        fmt = (
            "<green>{time:HH:mm:ss}</green> "
            "| <level>{level: <8}</level> "
            "| <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
            "— <level>{message}</level>"
        )
        logger.add(
            sys.stderr,
            format=fmt,
            level=level,
            colorize=True,
            enqueue=True,
        )


__all__ = ["setup_logger"]
