---
name: arclith-audit
description: Audit an existing Arclith project for architecture, CLI provenance, manifests, configuration, tests, transport contracts, persistence guarantees, security, and deployment readiness. Use for reviews, migrations, health checks, upgrade planning, or diagnosing an Arclith project; remain read-only unless fixes are requested.
license: Apache-2.0
metadata:
  author: karned-agency
  version: "0.1.0"
---

# Arclith Audit

Produce an evidence-backed assessment of the current project. An audit is read-only by default: do not regenerate, upgrade, install dependencies, or edit files unless the user also requests fixes.

## Collect evidence

Read repository instructions and inspect the worktree. Record the current branch and unrelated changes. Then run non-mutating checks:

```bash
arclith-cli version
arclith-cli capabilities --json
arclith-cli blueprints --json
arclith-cli status --json
arclith-cli doctor
arclith-cli history
```

If a command is unavailable or fails, capture the exact boundary instead of substituting assumptions. Inspect:

- `pyproject.toml`, lock files, supported Python version, and Arclith dependency range;
- `arclith.recipe.yaml`, `.arclith/features/`, and `.arclith/blueprints/`;
- `config/` and adapter activation;
- `src/<package>/{domain,application,adapters,infrastructure}`;
- composition roots and runtime entrypoints;
- unit, integration, protocol, and deployment tests;
- Docker, Compose, Kubernetes, CI, release, and user documentation when in scope.

Read [references/audit-checklist.md](references/audit-checklist.md) for the applicable areas.

## Evaluate actual guarantees

Compare code, recipe, manifests, configuration, dependencies, and documentation. Flag drift only with a concrete mismatch. Check that:

- domain code remains independent of transports and concrete providers;
- application use cases depend on ports and typed contracts;
- adapters implement protocol or provider details without duplicating domain models;
- infrastructure owns composition and configuration;
- configured adapters are installed, wired, documented, and tested;
- memory adapters are not presented as durable or multi-process;
- secrets are referenced, not committed or emitted;
- public HTTP statuses and responses are explicit;
- deployment claims are backed by runtime evidence.

Do not call a capability absent simply because its conventional file name differs. Use the CLI status, manifests, imports, and composition together.

## Report findings for action

Lead with the conclusion, then list findings by severity and evidence. For each actionable finding include:

1. the affected file or observed command output;
2. the architectural, functional, security, or operational impact;
3. the smallest durable remediation;
4. the relevant Arclith CLI command or documentation path;
5. what must be tested after the fix.

Separate confirmed defects, risks, optional improvements, and unverified external behavior. Do not inflate style preferences into architecture failures.

When the user requests fixes, preserve unrelated work, preview supported CLI mutations with `--dry-run`, implement focused changes, and use the relevant Arclith workflow. Re-run the audit checks and targeted validation afterward.
