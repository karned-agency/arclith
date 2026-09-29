from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from arclith import CommandDispatcher, command
from arclith.adapters.inbound.fastapi.command_bus import build_command_bus_router


class TodoUsecases:
    def __init__(self) -> None:
        self.calls: list[tuple[Mapping[str, Any], Mapping[str, str]]] = []

    @command("todo.create")
    async def create(self, payload: Mapping[str, Any], headers: Mapping[str, str]) -> None:
        self.calls.append((payload, headers))


class FailingUsecases:
    @command("todo.fail")
    async def fail(self, payload: Mapping[str, Any], headers: Mapping[str, str]) -> None:
        raise ValueError("domain rejected the payload")


def _client(dispatcher: CommandDispatcher, **kwargs: Any) -> TestClient:
    app = FastAPI()
    app.include_router(build_command_bus_router(dispatcher, **kwargs))
    return TestClient(app)


def test_command_bus_router_dispatches_to_matching_usecase() -> None:
    usecases = TodoUsecases()
    dispatcher = CommandDispatcher(handlers=[usecases])
    client = _client(dispatcher)

    response = client.post(
        "/commands/todo.create",
        json={"title": "write docs"},
        headers={"correlation_id": "corr-1"},
    )

    assert response.status_code == 202
    assert response.json() == {"status": "accepted", "command_type": "todo.create"}
    assert usecases.calls == [
        ({"title": "write docs"}, {"correlation_id": "corr-1"})
    ]


def test_command_bus_router_returns_404_for_unknown_command() -> None:
    dispatcher = CommandDispatcher()
    client = _client(dispatcher)

    response = client.post("/commands/unknown.command", json={})

    assert response.status_code == 404


def test_command_bus_router_returns_400_for_non_object_payload() -> None:
    dispatcher = CommandDispatcher(handlers=[TodoUsecases()])
    client = _client(dispatcher)

    response = client.post("/commands/todo.create", json=[1, 2, 3])

    assert response.status_code == 400


def test_command_bus_router_returns_400_for_malformed_json() -> None:
    dispatcher = CommandDispatcher(handlers=[TodoUsecases()])
    client = _client(dispatcher)

    response = client.post(
        "/commands/todo.create",
        content=b"{not-json",
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 400


def test_command_bus_router_maps_domain_errors_via_error_mappings() -> None:
    dispatcher = CommandDispatcher(handlers=[FailingUsecases()])
    client = _client(
        dispatcher,
        error_mappings=[(ValueError, 409, "Conflict")],
    )

    response = client.post("/commands/todo.fail", json={})

    assert response.status_code == 409


def test_command_bus_router_reraises_unmapped_exceptions() -> None:
    dispatcher = CommandDispatcher(handlers=[FailingUsecases()])
    client = _client(dispatcher)

    try:
        client.post("/commands/todo.fail", json={})
    except ValueError as exc:
        assert "domain rejected" in str(exc)
    else:
        raise AssertionError("expected ValueError to propagate")

