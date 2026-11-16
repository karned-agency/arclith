from __future__ import annotations

import logging
from typing import Any

import pytest

from arclith.domain.ports.outbound.logger import Logger, LogLevel
from arclith.infrastructure.uvicorn_logging import UvicornLogInterceptHandler


class CapturingLogger(Logger):
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def log(self, level: LogLevel, message: str, **metadata: Any) -> None:
        self.records.append({"level": level, "message": message, "metadata": metadata})


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        (logging.DEBUG, LogLevel.DEBUG),
        (logging.INFO, LogLevel.INFO),
        (logging.WARNING, LogLevel.WARNING),
        (logging.ERROR, LogLevel.ERROR),
        (logging.CRITICAL, LogLevel.CRITICAL),
        (logging.NOTSET, LogLevel.INFO),
    ],
)
def test_interceptor_preserves_levels_and_formats_arguments(
    level: int, expected: LogLevel
) -> None:
    logger = CapturingLogger()
    record = logging.LogRecord(
        "uvicorn.error", level, __file__, 1, "server %s", ("started",), None
    )

    UvicornLogInterceptHandler(logger).emit(record)

    assert logger.records == [
        {
            "level": expected,
            "message": "server started",
            "metadata": {"component": "uvicorn.error"},
        }
    ]


def test_interceptor_preserves_exception_traceback() -> None:
    logger = CapturingLogger()
    try:
        raise ValueError("server failed")
    except ValueError as exc:
        record = logging.LogRecord(
            "uvicorn.error",
            logging.ERROR,
            __file__,
            1,
            "request failed",
            (),
            (type(exc), exc, exc.__traceback__),
        )

    UvicornLogInterceptHandler(logger).emit(record)

    assert logger.records[0]["level"] == LogLevel.ERROR
    assert logger.records[0]["message"].startswith("request failed\nTraceback")
    assert "ValueError: server failed" in logger.records[0]["message"]
    assert logger.records[0]["metadata"] == {"component": "uvicorn.error"}
