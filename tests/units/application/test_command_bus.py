from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from arclith.application.command_bus import (
    CommandDispatcher,
    CommandEnvelope,
    InvalidCommandMessageError,
    UnknownCommandError,
    command,
    decode_command_message,
    encode_command_message,
)


class TodoUsecases:
    """Usecase de test groupant plusieurs commandes sur une seule classe."""

    def __init__(self) -> None:
        self.calls: list[tuple[Mapping[str, Any], Mapping[str, str]]] = []

    @command("todo.create")
    async def create(self, payload: Mapping[str, Any], headers: Mapping[str, str]) -> None:
        self.calls.append((payload, headers))

    def _validate(self, payload: Mapping[str, Any]) -> None:
        """Méthode non taguée — ne doit jamais être enregistrée."""


async def test_command_dispatcher_invokes_matching_handler() -> None:
    usecases = TodoUsecases()
    dispatcher = CommandDispatcher([usecases])

    await dispatcher.dispatch(
        CommandEnvelope(
            command_type="todo.create",
            payload={"title": "write docs"},
            headers={"correlation_id": "corr-1"},
        )
    )

    assert dispatcher.command_types == ("todo.create",)
    assert usecases.calls == [({"title": "write docs"}, {"correlation_id": "corr-1"})]


async def test_command_dispatcher_rejects_unknown_command() -> None:
    dispatcher = CommandDispatcher()

    with pytest.raises(UnknownCommandError, match="todo.create"):
        await dispatcher.dispatch(CommandEnvelope(command_type="todo.create", payload={}))


def test_command_dispatcher_rejects_duplicate_handler() -> None:
    dispatcher = CommandDispatcher([TodoUsecases()])

    with pytest.raises(ValueError, match="deja enregistre"):
        dispatcher.register_handlers(TodoUsecases())


def test_command_message_round_trip() -> None:
    envelope = CommandEnvelope(
        command_type="todo.create",
        payload={"title": "write docs"},
        headers={"correlation_id": "corr-1"},
    )

    decoded = decode_command_message(
        encode_command_message(envelope),
        headers=envelope.headers,
        fallback_command_type="fallback",
    )

    assert decoded == envelope


def test_command_message_can_use_header_command_type_for_raw_payload() -> None:
    decoded = decode_command_message(
        b'{"title": "write docs"}',
        headers={"command_type": "todo.create"},
        fallback_command_type="fallback",
    )

    assert decoded.command_type == "todo.create"
    assert decoded.payload == {"title": "write docs"}


def test_command_message_rejects_invalid_json_payload() -> None:
    with pytest.raises(InvalidCommandMessageError, match="JSON invalide"):
        decode_command_message(b"{", headers={}, fallback_command_type="todo.create")

    with pytest.raises(InvalidCommandMessageError, match="objet JSON"):
        decode_command_message(b'{"payload": []}', headers={}, fallback_command_type="todo.create")


class EntityUsecases:
    """Usecase de test groupant plusieurs commandes sur une seule classe."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, Mapping[str, Any]]] = []

    @command("create-entity")
    async def create(self, payload: Mapping[str, Any], headers: Mapping[str, str]) -> None:
        self.calls.append(("create", payload))

    @command("update-entity")
    async def update(self, payload: Mapping[str, Any], headers: Mapping[str, str]) -> None:
        self.calls.append(("update", payload))

    def _validate(self, payload: Mapping[str, Any]) -> None:
        """Méthode non taguée — ne doit jamais être enregistrée."""


def test_command_decorator_requires_non_empty_name() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        command("   ")


async def test_command_dispatcher_register_handlers_collects_tagged_methods_only() -> None:
    usecases = EntityUsecases()
    dispatcher = CommandDispatcher()

    dispatcher.register_handlers(usecases)

    assert dispatcher.command_types == ("create-entity", "update-entity")


async def test_command_dispatcher_dispatches_to_tagged_bound_method() -> None:
    usecases = EntityUsecases()
    dispatcher = CommandDispatcher(handlers=[usecases])

    await dispatcher.dispatch(
        CommandEnvelope(command_type="create-entity", payload={"name": "acme"})
    )

    assert usecases.calls == [("create", {"name": "acme"})]


async def test_command_dispatcher_registers_all_tagged_methods_across_usecases() -> None:
    entity_usecases = EntityUsecases()
    todo_usecases = TodoUsecases()

    dispatcher = CommandDispatcher(handlers=[entity_usecases, todo_usecases])

    assert dispatcher.command_types == ("create-entity", "todo.create", "update-entity")


def test_command_dispatcher_register_handlers_rejects_duplicate_command_type() -> None:
    dispatcher = CommandDispatcher()
    dispatcher.register_handlers(EntityUsecases())

    with pytest.raises(ValueError, match="deja enregistre"):
        dispatcher.register_handlers(EntityUsecases())
