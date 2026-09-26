---
name: arclith-agent
description: Create or evolve an Arclith agent with LangGraph, typed state, application ports, optional LLM providers, persistence, tools, and observability. Use for agent graphs, AI workflows, LLM configuration, memory, checkpoints, Agent Server, and production agent runtime requests.
license: Apache-2.0
metadata:
  author: karned-rekipe
  version: "0.1.0"
---

# Arclith Agent

Build an agent as an inbound orchestration surface over explicit application capabilities. Keep domain behavior and outbound dependencies usable without LangGraph or a particular model provider.

## Discover the current project and catalog

Read repository instructions and inspect the worktree. Run:

```bash
arclith-cli version
arclith-cli capabilities --json
arclith-cli status --json
arclith-cli doctor
```

Inspect the generated graph entrypoint, state and context, nodes, tools, application ports, configuration, `langgraph.json`, dependency extras, and current tests. Read [references/agent-playbook.md](references/agent-playbook.md) before selecting LLM, persistence, observability, or runtime options.

## Design boundaries before graph topology

1. Identify the user-visible agent outcome and the application use cases it needs.
2. Define typed commands, results, and outbound ports independently of prompts and providers.
3. Keep graph state small, typed, serializable, and versionable. Use message-compatible state only when the chat or Agent Server contract needs it.
4. Make each node responsible for one decision or application call. Keep routing explicit and testable.
5. Wrap business actions as tools that call application ports; do not let tools reach concrete repositories, vendor SDKs, or arbitrary infrastructure globals.
6. Separate prompt text, parsing, presentation, policy, persistence, and provider configuration.

Do not hide a workflow engine, business state machine, or durable job protocol inside generic graph transitions. Use the relevant Arclith domain blueprint or outbound port when the requirement is not intrinsically conversational.

## Add capabilities explicitly

Use `add-adapter --yes --dry-run` in non-interactive work before applying each supported capability:

- `agent/langgraph` for the graph structure and runtime entrypoint;
- one `llm` adapter only when the graph actually calls a model;
- `agent-persistence/langgraph` when thread checkpoints or cross-thread memory are required;
- secrets for provider credentials;
- observability when traces or metrics are requested and their data policy is known.

Keep the initial graph executable without a model call when practical. Do not choose OpenAI, Anthropic, LM Studio, LangSmith, or any other provider merely because it is available. Never invent, echo, log, or commit an API key. A local development checkpointer or in-memory store is not production durability.

For production, distinguish:

- graph state within one run;
- thread checkpoints across runs;
- cross-thread memory or stores;
- business persistence owned by repositories;
- the Agent Server or durable runtime lifecycle.

These are separate concerns and may require separate backends.

## Verify in layers

1. Test domain and application behavior without LangGraph or a live LLM.
2. Compile the graph and test nodes and routing with deterministic fakes.
3. Test tool argument validation, authorization, typed results, and failure mapping.
4. Run the local graph API or selected runtime and execute a real thread or run.
5. If a live model is part of acceptance, verify the configured provider and model explicitly while keeping credentials out of output.
6. For persistence, restart the relevant process and prove that the required thread or memory state survives using the configured durable backend.
7. Run `arclith-cli status --json` and `arclith-cli doctor` after all changes.

Report which layers were verified. Do not equate a compiled graph, a fake-model test, or a successful development server start with a production-ready agent.
