from __future__ import annotations

import inspect
import json
from collections.abc import Awaitable, Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

_COMMAND_ATTR = "__arclith_command_type__"

CommandMethod = Callable[[Mapping[str, Any], Mapping[str, str]], Awaitable[None]]


def command(name: str) -> Callable[[CommandMethod], CommandMethod]:
    """Tag a bound method as the handler for a given command type.

    The tagged method must accept ``(payload, headers)``. Declaring a
    non-empty command name is mandatory — an empty/blank name raises
    immediately at import time.

    Usage::

        class EntityUsecases:
            @command("create-entity")
            async def create(self, payload, headers): ...

        dispatcher = CommandDispatcher(handlers=[EntityUsecases(repo, logger)])
    """
    normalized = name.strip()
    if not normalized:
        raise ValueError("command name must not be empty")

    def decorator(func: CommandMethod) -> CommandMethod:
        setattr(func, _COMMAND_ATTR, normalized)
        return func

    return decorator


class CommandBusError(Exception):
    """Base error for command-bus dispatch and serialization failures."""


class UnknownCommandError(CommandBusError):
    """Raised when no registered handler matches a command type."""


class InvalidCommandMessageError(CommandBusError):
    """Raised when a broker message cannot be decoded into a command envelope."""


@dataclass(frozen=True)
class CommandEnvelope:
    command_type: str
    payload: Mapping[str, Any]
    headers: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.command_type.strip():
            raise ValueError("command_type est requis")


class CommandDispatcher:
    """Dispatch command envelopes to methods tagged with ``@command(...)``.

    Any plain object exposing one or more ``@command(...)``-tagged methods can
    be registered — no base class required. A single object can expose several
    commands (e.g. a use case class with ``create``/``update``/``read``), which
    avoids one dedicated handler class per command.
    """

    def __init__(self, handlers: Iterable[Any] = ()) -> None:
        self._handlers: dict[str, CommandMethod] = {}
        for obj in handlers:
            self.register_handlers(obj)

    @property
    def command_types(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))

    def register(self, command_type: str, method: CommandMethod) -> None:
        normalized = command_type.strip()
        if not normalized:
            raise ValueError("command_type est requis")
        if normalized in self._handlers:
            raise ValueError(f"handler deja enregistre pour command_type={normalized}")
        self._handlers[normalized] = method

    def register_handlers(self, obj: Any) -> None:
        """Scan ``obj`` for ``@command(...)``-tagged methods and register each one.

        Works with any object — no base class required. Only bound methods
        carrying the ``@command`` metadata are registered; everything else is
        ignored.
        """
        for _, method in inspect.getmembers(obj, predicate=inspect.ismethod):
            command_type = getattr(method, _COMMAND_ATTR, None)
            if command_type is not None:
                self.register(command_type, method)

    async def dispatch(self, envelope: CommandEnvelope) -> None:
        handler = self._handlers.get(envelope.command_type)
        if handler is None:
            raise UnknownCommandError(f"Aucun handler pour command_type={envelope.command_type}")
        await handler(envelope.payload, envelope.headers)


def encode_command_message(envelope: CommandEnvelope) -> bytes:
    body = {
        "type": envelope.command_type,
        "payload": dict(envelope.payload),
    }
    return json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def decode_command_message(
    body: bytes,
    *,
    headers: Mapping[str, str],
    fallback_command_type: str,
) -> CommandEnvelope:
    try:
        decoded = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidCommandMessageError("message command-bus JSON invalide") from exc

    if isinstance(decoded, dict) and "payload" in decoded:
        payload = decoded["payload"]
        command_type = str(decoded.get("type") or decoded.get("command_type") or fallback_command_type)
    else:
        payload = decoded
        command_type = headers.get("command_type", fallback_command_type)

    if not isinstance(payload, dict):
        raise InvalidCommandMessageError("message command-bus payload doit etre un objet JSON")

    return CommandEnvelope(command_type=command_type, payload=payload, headers=dict(headers))
