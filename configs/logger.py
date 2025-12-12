"""Application-wide logging utilities."""

from __future__ import annotations

import logging
import os
from typing import Optional

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv(
    "LOG_FORMAT",
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


class AppLogger:
    """Factory for configured loggers with optional structured prefixes."""

    def __init__(self, level: str = LOG_LEVEL, fmt: str = LOG_FORMAT) -> None:
        self.level = getattr(logging, level, logging.INFO)
        self.format = fmt
        self._configure_root()

    def _configure_root(self) -> None:
        logging.basicConfig(level=self.level, format=self.format)

    def get_logger(self, name: str, *, extra_prefix: Optional[str] = None) -> logging.Logger:
        """Return a logger with optional prefix injected in messages."""
        logger = logging.getLogger(name)
        logger.setLevel(self.level)

        if extra_prefix:
            prefix = extra_prefix.strip()
            class PrefixAdapter(logging.LoggerAdapter):
                def process(self, msg, kwargs):  # type: ignore[override]
                    return f"[{prefix}] {msg}", kwargs
            return PrefixAdapter(logger, {})

        return logger

    def log_kv(self, logger: logging.Logger, level: int, message: str, **kv: object) -> None:
        """Log a message with key=value pairs appended."""
        kv_part = " ".join(f"{k}={v}" for k, v in kv.items())
        full_msg = f"{message} | {kv_part}" if kv_part else message
        logger.log(level, full_msg)


app_logger = AppLogger()


__all__ = ["AppLogger", "app_logger"]
