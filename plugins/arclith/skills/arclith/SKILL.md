---
name: arclith
description: Initialize or evolve an Arclith project through its official CLI, blueprints, and capability catalog while preserving hexagonal boundaries. Use for broad Arclith requests, new services, entities, use cases, adapters, or when deciding which specialized Arclith workflow applies.
license: Apache-2.0
metadata:
  author: karned-rekipe
  version: "0.1.0"
---

# Arclith

Build a working Arclith project whose architecture, generated manifests, recipe, tests, and runtime evidence agree. Treat the installed CLI and the project's current files as the source of truth; do not rely on a remembered capability list.

## Establish the current state

1. Read the repository's agent instructions and contributor documentation before changing files.
2. Inspect the worktree and preserve unrelated work.
3. Use an installed `arclith-cli` when available. Otherwise invoke the published CLI as `uvx --from arclith-cli arclith-cli ...`.
4. Run `arclith-cli version`, `arclith-cli capabilities --json`, and `arclith-cli blueprints --json` before selecting commands or adapters.
5. In an existing project, run `arclith-cli status --json` and `arclith-cli doctor`. Inspect `arclith.recipe.yaml`, `.arclith/`, `config/`, `pyproject.toml`, the package under `src/`, and the relevant tests.

Do not run `init` inside an existing project or replace an existing composition root merely to match a starter example.

## Translate the request into explicit decisions

Determine only what the requested outcome needs:

- the domain concepts and invariants;
- a minimal, CRUD, append-only, or state-machine application blueprint;
- inbound surfaces such as API, MCP, command bus, channel, or agent;
- outbound capabilities such as repository, storage, cache, secrets, LLM, or observability;
- the local and production runtime expectations.

Ask for input only when a missing business or deployment choice would materially change the result. Never infer credentials, production endpoints, tenant identifiers, or a durable storage guarantee.

Read [references/workflow-selection.md](references/workflow-selection.md) when choosing the concrete Arclith path. For a focused request, also use the bundled `arclith-api`, `arclith-agent`, `arclith-deploy`, or `arclith-audit` workflow when the client exposes it.

## Generate through the CLI

Prefer Arclith commands over hand-written framework plumbing because the CLI also maintains recipes, manifests, dependencies, configuration, and generated documentation.

1. Initialize only the minimal project with `arclith-cli init <project> --dir <parent>`.
2. Add domain concepts with `add-entity` and explicit application behavior with `add-usecase` or `add-blueprint`.
3. Use `--dry-run` on `add-blueprint`, `add-adapter`, `expose-usecase`, `expose-feature`, and `replay` before a non-trivial mutation. Add `--yes` to an `add-adapter` dry-run in non-interactive work so the preview cannot stop at a prompt.
4. Add only capabilities returned by `capabilities --json` and only adapters valid for those capabilities.
5. Expose a use case or feature only after the corresponding inbound adapter exists.
6. Review the generated diff before filling in business fields, invariants, policies, mappings, and composition.

Do not copy a generated adapter from another project, invent catalogue parameters, or manually edit `.arclith` manifests to simulate a successful command.

## Preserve the architecture

Keep these responsibilities separate:

| Layer | Responsibility |
|---|---|
| `domain` | Business entities, values, errors, invariants, and provider-neutral ports |
| `application` | Commands, queries, results, use cases, and orchestration of domain ports |
| `adapters` | Protocol mapping and concrete technology implementations |
| `infrastructure` | Configuration, factories, dependency wiring, and runtime composition |

Transport handlers call application ports, not concrete repositories. Domain behavior must not depend on FastAPI, FastMCP, RabbitMQ, LangGraph, database clients, HTTP calls, environment parsing, or deployment code. Keep request DTOs, application commands, domain entities, and response DTOs distinct when their contracts differ.

Preserve these operational invariants:

- no real secret in code, recipes, manifests, configuration committed to Git, logs, or examples;
- no production claim based only on generated files or a green unit test;
- no in-memory adapter described as durable or multi-process safe;
- no provider-specific workaround in the domain when an outbound port is required;
- no unrequested adapter, transport, or runtime added "for later".

## Prove completion

After changes:

1. Run `arclith-cli status --json` and `arclith-cli doctor`.
2. Synchronize with the project's documented `uv` command and run its targeted tests, then its standard lint, type, and test gates when available.
3. Exercise the changed boundary: domain use case, HTTP operation, MCP tool, message handler, graph run, or container endpoint.
4. Confirm that `arclith.recipe.yaml`, `.arclith/` manifests, dependency extras, configuration, code, tests, and documentation describe the same design.
5. Report commands executed, observable results, assumptions, and anything not validated against a live external system.
