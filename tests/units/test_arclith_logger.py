import logging
from pathlib import Path

import pytest

from arclith import Arclith
from arclith.adapters.outbound.console.logger import ConsoleLogger
from arclith.adapters.outbound.noop.observability import NoOpObservabilityRuntime
from arclith.infrastructure.uvicorn_logging import UvicornLogInterceptHandler


def test_arclith_logger_uses_configured_console_adapter(tmp_path: Path) -> None:
    config_dir = tmp_path / "config" / "adapters"
    config_dir.mkdir(parents=True)
    (config_dir / "adapters.yaml").write_text(
        "logger: console\n"
        "repository: memory\n"
        "observability:\n"
        "  enabled: []\n",
        encoding="utf-8",
    )

    arclith = Arclith(tmp_path / "config")
    logger = arclith.logger

    assert isinstance(logger, ConsoleLogger)
    assert arclith.logger is logger


def test_arclith_configures_server_logging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arclith = Arclith(tmp_path)
    runtime = NoOpObservabilityRuntime()
    arclith.__dict__["_observability_runtime"] = runtime
    names = ("uvicorn", "uvicorn.access", "uvicorn.error", "watchfiles")
    logs = {name: logging.getLogger(name) for name in names}
    for log in logs.values():
        monkeypatch.setattr(log, "handlers", [logging.NullHandler()])
        monkeypatch.setattr(log, "level", logging.WARNING)
        monkeypatch.setattr(log, "propagate", True)

    arclith._setup_uvicorn_logging()

    handler = logs["uvicorn"].handlers[0]
    assert isinstance(handler, UvicornLogInterceptHandler)
    assert handler._logger is arclith.logger
    assert handler._correlation is runtime.correlation
    for log in logs.values():
        assert log.handlers == [handler]
        assert log.level == logging.DEBUG
        assert log.propagate is False
