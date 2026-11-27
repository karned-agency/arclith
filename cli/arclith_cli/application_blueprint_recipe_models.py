"""Typed persisted contracts for application-blueprint recipe steps."""

from __future__ import annotations

import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from arclith_cli.state_machine_migration import MIGRATION_KIND

_SHA256_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


class MigrateBlueprintRecipeArgs(BaseModel):
    """Arguments recorded for one additive state-machine migration."""

    model_config = ConfigDict(extra="forbid", strict=True)

    blueprint: Literal["state-machine"]
    entity: Annotated[str, Field(min_length=1)]
    feature: Annotated[str, Field(min_length=1)]
    migration: str
    from_parameters_digest: str
    operations: list[str]
    blueprint_version: int
    template_digest: str
    parameters: dict[str, object]
    parameters_digest: str

    @field_validator("entity", "feature")
    @classmethod
    def require_non_blank_name(cls, value: str) -> str:
        """Reject names which only contain whitespace."""

        if not value.strip():
            raise ValueError("must not be blank")
        return value

    @field_validator("migration")
    @classmethod
    def require_supported_migration(cls, value: str) -> str:
        """Reject migrations other than the additive state-machine contract."""

        if value != MIGRATION_KIND:
            raise ValueError("must be the supported state-machine migration kind")
        return value

    @field_validator(
        "from_parameters_digest",
        "template_digest",
        "parameters_digest",
    )
    @classmethod
    def require_sha256_digest(cls, value: str) -> str:
        """Accept only complete SHA-256 digests recorded by the CLI."""

        if not _SHA256_DIGEST.fullmatch(value):
            raise ValueError("must be a sha256 digest")
        return value
