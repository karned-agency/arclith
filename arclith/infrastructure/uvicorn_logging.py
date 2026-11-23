"""Bridge standard Uvicorn records to the configured application logger."""

from __future__ import annotations

import logging
import traceback
from collections.abc import Mapping

from arclith.domain.ports.outbound.logger import Logger, LogLevel
from arclith.domain.ports.outbound.observability import CorrelationContextPort

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
        # Uvicorn access records contain (client, method, target, version, status).
        # Sanitize before formatting so query values never reach any logger sink.
        # Copy the record to preserve it for other logging handlers.
        args = record.args
        if (
            record.name == "uvicorn.access"
            and isinstance(args, tuple)
            and len(args) == 5
            and isinstance(args[2], str)
        ):
            target = args[2].split("?", 1)[0].split("#", 1)[0]
            record = logging.makeLogRecord(record.__dict__.copy())
            record.args = (*args[:2], target, *args[3:])
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
        self._logger.log(
            _LEVEL_MAP.get(record.levelname, LogLevel.INFO),
            message,
            **injected,
        )

