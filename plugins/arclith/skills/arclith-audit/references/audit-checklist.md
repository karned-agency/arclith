# Arclith audit checklist

Apply only sections relevant to the request. Prefer a few high-confidence findings over a long speculative list.

## Project and provenance

- CLI version is known and compatible with the project's generated artifacts.
- `status --json`, `doctor`, and `history` are readable.
- Recipe steps, feature manifests, adapter blueprints, code, and active configuration agree.
- Generated files do not contain machine-specific absolute paths or secrets.
- Dependency extras match the adapters actually imported and configured.

## Hexagonal boundaries

- Domain holds business concepts, invariants, errors, and provider-neutral ports.
- Application commands, queries, results, and use cases are distinct from transport DTOs.
- Inbound adapters call application ports rather than repositories or database clients.
- Outbound adapters implement domain or application ports without leaking provider types inward.
- Infrastructure owns factories, settings, lifecycle, and dependency wiring.
- Inter-service HTTP, SDK, broker, or model-provider calls do not originate from domain code.

## Behavior and protocols

- Business behavior has focused unit tests independent of external systems.
- FastAPI operations declare status and error responses and validate DTO mappings.
- MCP tools have stable names, typed inputs, bounded outputs, and safe errors.
- Message handlers define command identity, acknowledgement, retries, deduplication, and correlation.
- Agent graphs keep typed state, explicit routing, application-backed tools, and deterministic tests.

## Data and concurrency

- Repository guarantees match usage: transactions, mapping, tenancy, and optimistic locking.
- State-machine transitions use durable compare-and-swap where concurrency matters.
- Append-only ingestion has stable identity and durable idempotency where required.
- Shared cache, idempotency, checkpoint, and store needs do not use process-local memory in production.
- Persistent-data migrations and rollback procedures are explicit.

## Security and operations

- Credentials and private endpoints are absent from Git, examples, recipes, logs, and client code.
- Authentication, tenant, and license checks occur at the intended inbound boundary.
- Images contain no build-time secret and run with least privilege supported by the target.
- Health, readiness, graceful shutdown, resource limits, and observability match the runtime.
- Documentation names local-only fakes and distinguishes generated, tested, deployed, and live-verified states.

## Evidence commands

Use project-documented checks. Typical evidence includes:

```bash
arclith-cli status --json
arclith-cli doctor
uv sync --frozen
uv run pytest
```

Add lint, type checking, coverage, docs, image build, and protocol smoke tests when the repository defines or the audit scope requires them.
