from __future__ import annotations

import logging
import traceback
from collections.abc import Mapping
from typing import Any

from arclith.domain.ports.outbound.logger import Logger, LogLevel
from arclith.domain.ports.outbound.observability import CorrelationContextPort

UVICORN_LOG_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {},
    "loggers": {
        "uvicorn": {"handlers": [], "propagate": False},
        "uvicorn.access": {"handlers": [], "propagate": False},
        "uvicorn.error": {"handlers": [], "propagate": False},
    },
}
_LEVEL_MAP: dict[str, LogLevel] = {
    "DEBUG": LogLevel.DEBUG,
    "INFO": LogLevel.INFO,
    "WARNING": LogLevel.WARNING,
    "ERROR": LogLevel.ERROR,
    "CRITICAL": LogLevel.CRITICAL,
}


class UvicornLogInterceptHandler(logging.Handler):
    def __init__(
        self,
        logger: Logger,
        correlation: CorrelationContextPort | None = None,
    ) -> None:
        super().__init__()
        self._logger = logger
        self._correlation = correlation

    def emit(self, record: logging.LogRecord) -> None:
        message = record.getMessage()
        if record.exc_info:
            exc = record.exc_info[1]
            tb = "".join(traceback.format_exception(exc))
            message = f"{message}\n{tb}"
        injected: Mapping[str, str | bool] = {}
        if self._correlation is not None:
            injected = self._correlation.from_log_record(record)
            if not injected:
                injected = self._correlation.current()
        metadata = dict(injected)
        metadata["component"] = record.name
        self._logger.log(
            _LEVEL_MAP.get(record.levelname, LogLevel.INFO),
            message,
            **metadata,
        )


def setup_uvicorn_logging(
    logger: Logger,
    correlation: CorrelationContextPort | None = None,
) -> None:
    handler = UvicornLogInterceptHandler(logger, correlation)
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error", "watchfiles"):
        log = logging.getLogger(name)
        log.setLevel(logging.DEBUG)
        log.handlers = [handler]
        log.propagate = False
