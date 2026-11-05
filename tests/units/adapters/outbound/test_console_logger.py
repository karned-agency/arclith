import json
import logging
import subprocess
import sys
from collections.abc import Iterator, Mapping
from typing import Any

import pytest

from arclith.adapters.outbound.console import logger as console_logger
from arclith.adapters.outbound.console.logger import ConsoleLogger
from arclith.arclith import _UvicornLogInterceptHandler
from arclith.domain.ports.outbound.logger import LogLevel
from arclith.domain.ports.outbound.observability import (
    CorrelationContextPort,
    LogRecordPort,
)


@pytest.fixture
def captured_logs() -> Iterator[list[str]]:
    messages: list[str] = []
    handler_id = console_logger.loguru_logger.add(
        messages.append,
        format=console_logger._FORMAT,
        colorize=False,
        serialize=True,
    )
    try:
        yield messages
    finally:
        console_logger.loguru_logger.remove(handler_id)


def test_console_logger_enriches_metadata_with_current_trace(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    class BoundLogger:
        def info(self, message: str) -> None:
            captured["message"] = message

    def fake_bind(**kwargs: Any) -> BoundLogger:
        captured["bind"] = kwargs
        return BoundLogger()

    monkeypatch.setattr(console_logger.loguru_logger, "bind", fake_bind)

    correlation = type(
        "Correlation",
        (),
        {
            "current": lambda self: {
                "trace_id": "trace",
                "span_id": "span",
                "trace_sampled": True,
            }
        },
    )()
    ConsoleLogger(correlation=correlation).log(  # type: ignore[arg-type]
        LogLevel.INFO,
        "hello",
        request_id="req-1",
        trace_id="application-trace",
        span_id="application-span",
        trace_sampled=False,
    )

    assert captured["message"] == "hello"
    assert captured["bind"]["meta"] == {
        "trace_id": "trace",
        "span_id": "span",
        "trace_sampled": True,
        "request_id": "req-1",
    }


@pytest.mark.parametrize("level", list(LogLevel))
def test_console_logger_detects_caller_for_all_levels(
    captured_logs: list[str],
    level: LogLevel,
) -> None:
    class CallingService:
        def emit(self) -> None:
            getattr(ConsoleLogger(), level.value.lower())("hello", count=12)

    CallingService().emit()

    entry = json.loads(captured_logs[0])
    assert entry["record"]["level"]["name"] == level.value
    assert entry["record"]["extra"]["component"] == "CallingService"
    assert entry["record"]["extra"]["meta"] == {"count": 12}
    assert "| CallingService | hello | {'count': 12}" in entry["text"]
    assert "\033[" not in entry["text"]


def test_console_logger_detects_caller_for_direct_log(
    captured_logs: list[str],
) -> None:
    class CallingAdapter:
        def emit(self) -> None:
            ConsoleLogger().log(LogLevel.INFO, "direct")

    CallingAdapter().emit()

    assert json.loads(captured_logs[0])["record"]["extra"]["component"] == "CallingAdapter"


def test_console_logger_skips_logger_subclasses(captured_logs: list[str]) -> None:
    class WrappedLogger(ConsoleLogger):
        def info(self, message: str, **metadata: Any) -> None:
            super().info(message, **metadata)

    class CallingService:
        def emit(self) -> None:
            WrappedLogger().info("wrapped")

    CallingService().emit()

    assert json.loads(captured_logs[0])["record"]["extra"]["component"] == "CallingService"


def test_console_logger_detects_falsey_calling_instance(
    captured_logs: list[str],
) -> None:
    class CallingService:
        def __bool__(self) -> bool:
            return False

        def emit(self) -> None:
            ConsoleLogger().info("hello")

    CallingService().emit()

    assert json.loads(captured_logs[0])["record"]["extra"]["component"] == "CallingService"


def test_console_logger_uses_explicit_component(captured_logs: list[str]) -> None:
    ConsoleLogger().info("external", component="external.worker", count=12)

    extra = json.loads(captured_logs[0])["record"]["extra"]
    assert extra["component"] == "external.worker"
    assert extra["meta"] == {"component": "external.worker", "count": 12}


@pytest.mark.parametrize("component", [None, "", 12])
def test_console_logger_preserves_non_name_component_metadata(
    captured_logs: list[str],
    component: object,
) -> None:
    class CallingService:
        def emit(self) -> None:
            ConsoleLogger().info("hello", component=component)

    CallingService().emit()

    extra = json.loads(captured_logs[0])["record"]["extra"]
    assert extra["component"] == "CallingService"
    assert extra["meta"] == {"component": component}


def test_console_logger_falls_back_when_frames_are_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    captured_logs: list[str],
) -> None:
    monkeypatch.setattr(console_logger.inspect, "currentframe", lambda: None)

    ConsoleLogger().info("global")

    assert json.loads(captured_logs[0])["record"]["extra"]["component"] == "Global"


def test_console_logger_falls_back_for_module_level_call() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from arclith import ConsoleLogger; ConsoleLogger().info('global')",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    entry = json.loads(result.stderr)
    assert entry["record"]["extra"]["component"] == "Global"
    assert "| Global | global | {}" in entry["text"]
    assert result.stdout == ""


def test_default_console_sink_emits_native_json_for_all_levels() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
from uuid import UUID
from arclith import ConsoleLogger
from arclith.domain.ports.outbound.logger import LogLevel

class CallingService:
    def emit(self):
        logger = ConsoleLogger()
        for level in LogLevel:
            logger.log(
                level,
                "first line\\r\\nsecond line",
                system_uuid=UUID("12345678-1234-5678-1234-567812345678"),
                batch={"count": 12},
            )

CallingService().emit()
""",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    lines = result.stderr.splitlines()
    assert result.stdout == ""
    assert len(lines) == len(LogLevel)
    assert "\033[" not in result.stderr
    for level, line in zip(LogLevel, lines, strict=True):
        entry = json.loads(line)
        assert set(entry) == {"text", "record"}
        record = entry["record"]
        assert record["level"]["name"] == level.value
        assert record["message"] == "first line\r\nsecond line"
        assert record["extra"]["component"] == "CallingService"
        assert record["extra"]["meta"] == {
            "system_uuid": "12345678-1234-5678-1234-567812345678",
            "batch": {"count": 12},
        }
        assert isinstance(record["time"]["timestamp"], (int, float))


def test_console_logger_exports_component_and_correlation(
    captured_logs: list[str],
) -> None:
    emitted: list[tuple[str, str, Mapping[str, object] | None]] = []

    class Correlation(CorrelationContextPort):
        def current(self) -> Mapping[str, str | bool]:
            return {"trace_id": "trace", "span_id": "span", "trace_sampled": True}

        def from_log_record(self, record: Any) -> Mapping[str, str | bool]:
            return {}

    class Records(LogRecordPort):
        def emit(
            self,
            level: str,
            body: str,
            *,
            attributes: Mapping[str, object] | None = None,
        ) -> None:
            emitted.append((level, body, attributes))

    class CallingService:
        def emit(self) -> None:
            logger = ConsoleLogger()
            logger.configure_observability(Correlation(), Records())
            logger.info("hello", count=12, trace_id="application-trace")

    CallingService().emit()

    assert emitted == [
        (
            "INFO",
            "hello",
            {
                "component": "CallingService",
                "count": 12,
                "trace_id": "trace",
                "span_id": "span",
                "trace_sampled": True,
            },
        )
    ]
    extra = json.loads(captured_logs[0])["record"]["extra"]
    assert extra["component"] == "CallingService"
    assert extra["meta"]["trace_id"] == "trace"
    assert "component" not in extra["meta"]


@pytest.mark.parametrize(
    "name",
    ["uvicorn", "uvicorn.access", "uvicorn.error", "watchfiles"],
)
def test_intercepted_logger_name_is_used_as_component(
    captured_logs: list[str],
    name: str,
) -> None:
    record = logging.LogRecord(name, logging.INFO, __file__, 1, "server log", (), None)

    _UvicornLogInterceptHandler(ConsoleLogger()).emit(record)

    assert json.loads(captured_logs[0])["record"]["extra"]["component"] == name
