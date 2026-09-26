# Agent playbook

Query the installed catalog first because adapters and parameters evolve:

```bash
arclith-cli capabilities --json
arclith-cli add-adapter --help
```

## Minimal graph

```bash
arclith-cli add-adapter --capability agent --adapter langgraph --yes --dry-run
arclith-cli add-adapter --capability agent --adapter langgraph --yes
uv sync
```

The generated graph is a structure to complete, not a finished business agent. Preserve its documented packages for nodes, tools, policies, parsers, presenters, persistence, and shared code.

Documentation: <https://arclith.karned.bzh/quickstarts/agent/>

## Model provider

Choose a provider from the live `llm` catalog only after the user or target environment establishes the requirement. Preview before applying:

```bash
arclith-cli add-adapter --capability llm --adapter <catalog-adapter> \
  --param model_name=<model-id> --yes --dry-run
```

Store credentials in the runtime's approved secret mechanism. Keep provider-specific construction in adapters or infrastructure and inject the provider-neutral LLM port into application or graph composition.

## Persistence

For local behavior, the catalog may offer memory checkpointers and stores:

```bash
arclith-cli add-adapter --capability agent-persistence --adapter langgraph \
  --param checkpointer=memory --param store=memory --yes --dry-run
```

Before production, select backends whose guarantees match the deployment, install only their optional extras, and prove lifecycle ownership. Agent Server-managed persistence must not be initialized and closed a second time by application code.

Documentation: <https://arclith.karned.bzh/capabilities/agent-persistence/>

## Observability

Observability remains optional. Disabled tracing must remain a complete no-op without provider imports, clients, network calls, or global SDK mutation. When enabled, redact prompts or content according to the application's data policy and preserve trace context across allowed boundaries without forwarding authorization headers.

Documentation: <https://arclith.karned.bzh/capabilities/observability/>

## Runtime acceptance

Use deterministic tests first. Then run the documented local Agent Server or Arclith durable runtime and verify:

- graph discovery and compilation;
- one successful run;
- one expected failure path;
- thread state retrieval;
- checkpoint survival when durability is required;
- graceful shutdown and restart;
- trace or metric evidence only when observability is enabled.
