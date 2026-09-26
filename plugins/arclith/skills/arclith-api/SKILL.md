---
name: arclith-api
description: Create or change an Arclith inbound surface such as FastAPI, FastMCP, or RabbitMQ while keeping protocol mapping outside the domain. Use for REST APIs, OpenAPI, MCP tools, message commands, endpoint exposure, HTTP contracts, auth, probes, and transport smoke tests.
license: Apache-2.0
metadata:
  author: karned-agency
  version: "0.1.0"
---

# Arclith API and transports

Expose existing application behavior through the requested transport without moving business rules into handlers or binding the domain to a protocol.

## Inspect before changing

Read repository instructions, then run:

```bash
arclith-cli version
arclith-cli capabilities --json
arclith-cli status --json
arclith-cli doctor
```

Inspect the inbound port and use case, current adapter manifests under `.arclith/`, adapter configuration, composition root, protocol mappings, and tests. If the application behavior does not yet exist, define the entity, command or query, result, port, use case, and domain errors before exposing it.

Read [references/transport-playbook.md](references/transport-playbook.md) for the selected surface.

## Choose the correct surface

- Use FastAPI for resource-oriented HTTP, browser or service clients, OpenAPI, and explicit status semantics.
- Use FastMCP for model-callable tools over the supported HTTP transports.
- Use RabbitMQ for asynchronous commands whose delivery, retry, deduplication, and acknowledgement semantics are explicit.
- Do not expose the same operation through every transport unless the user actually needs those contracts.

Query `capabilities --json` and command help rather than assuming that a remembered adapter, parameter, or projection is available. In particular, check which feature-level projections the installed CLI supports; fall back to explicit use-case exposure when no projection exists.

## Generate, then implement the contract

1. Add the requested inbound adapter with `add-adapter --yes --dry-run` in non-interactive work, review the plan, then apply it.
2. Preview `expose-usecase` or `expose-feature` with `--dry-run` before writing files.
3. Treat generated code as protocol scaffolding. Complete request validation, DTO-to-command mapping, result-to-response mapping, error translation, registration, and tests.
4. Keep the handler thin: parse and authorize, call the inbound port, translate the typed result or error.
5. Compose application ports and concrete outbound adapters in infrastructure, never in the domain or route/tool module.

For HTTP, declare successful `status_code` and error `responses` explicitly. Preserve `201` for creation when appropriate, `404` for missing resources, and `409` for optimistic-lock or state conflicts. Do not leak internal exceptions or persistence models into the public schema.

Add cross-cutting capabilities only when required:

- `http/idempotency` for safely retried mutations;
- `http/etag` for conditional versioned resources;
- `http/cache-control` for explicit cache semantics;
- `auth/keycloak`, tenant, and license policies for protected surfaces;
- `probe/server` for independently observable health and readiness.

Shared or multi-process behavior must not depend on an in-memory cache, idempotency store, repository, or broker fake.

## Verify the real boundary

Run `status --json`, `doctor`, and the project's targeted tests. Then start the actual transport and verify a representative successful request plus important error paths:

- FastAPI: inspect `/openapi.json`, call the operation, and verify status, body, headers, and validation errors.
- FastMCP: connect with a real MCP client or supported inspector and invoke the generated tool.
- RabbitMQ: publish a real test command to the configured local broker, observe handler execution, and verify acknowledgement or failure behavior.

Do not report an API, tool, or consumer as working from file generation alone. State clearly when an external identity provider, broker, or production endpoint was not exercised.
