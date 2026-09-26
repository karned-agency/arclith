# Workflow selection

Use the current CLI catalog before every choice:

```bash
arclith-cli capabilities --json
arclith-cli blueprints --json
```

If `arclith-cli` is not installed as a managed tool, prefix the same commands with `uvx --from arclith-cli`.

## Start from the business behavior

| User outcome | Application path | Next decision |
|---|---|---|
| One or more bespoke operations | `add-entity`, then `add-usecase` | Expose each selected use case through a transport |
| Conventional entity lifecycle | `add-entity --profile minimal`, then `add-blueprint crud` | Add a repository and optionally project the feature to FastAPI |
| Immutable facts or ingestion | `add-entity --profile append-only` | Compose an explicit append-only store and idempotency policy |
| Named lifecycle transitions | `add-entity --profile state-machine --spec <file>` | Implement durable compare-and-swap through an outbound port |
| Cross-cutting operation without an entity | `add-usecase <name> --no-entity` | Add only the ports the operation actually needs |

Use `add-blueprint <name> --entity <entity> --dry-run` when the entity already exists. A blueprint creates application behavior; it does not silently choose a transport or persistence technology.

## Add technical capabilities deliberately

Use `arclith-cli add-adapter --capability <capability> --adapter <adapter> --yes --dry-run` first in non-interactive work. Inspect the catalog entry and the generated plan before applying it with the required `--param` values and `--yes`.

Common sequences are:

- REST API: application behavior -> repository if needed -> `api/fastapi` -> `expose-usecase` or `expose-feature`.
- MCP: application behavior -> required outbound adapters -> `mcp/fastmcp` -> `expose-usecase --via fastmcp`.
- Asynchronous command: application behavior -> `command-bus/rabbitmq` -> `expose-usecase --via rabbitmq`.
- Agent: application ports -> `agent/langgraph` -> optional `llm` -> optional `agent-persistence` -> optional observability.
- Production container: functional service -> `probe/server` -> `runtime/docker-image` -> runtime secrets and external services.

Never select every production capability by default. Authentication, licensing, tenancy, Redis, Vault, durable persistence, and observability each require an explicit operational need and configuration.

## Existing project

Start with:

```bash
arclith-cli status --json
arclith-cli doctor
arclith-cli history
```

Use the recipe for provenance and replay, not as a substitute for inspecting current code and configuration. If the project drifted from generated manifests, diagnose the drift before replaying or regenerating anything.

## Authoritative documentation

- Overview: <https://karned-rekipe.github.io/arclith/>
- CLI guide: <https://karned-rekipe.github.io/arclith/cli-guide/>
- Capabilities: <https://karned-rekipe.github.io/arclith/capabilities/>
- Application blueprints: <https://karned-rekipe.github.io/arclith/blueprints/>
- Quickstarts: <https://karned-rekipe.github.io/arclith/quickstarts/>
