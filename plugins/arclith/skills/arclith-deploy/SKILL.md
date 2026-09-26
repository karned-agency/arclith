---
name: arclith-deploy
description: Package and deploy an Arclith service with its generated Docker runtime, probes, configuration, secrets, Compose, or Kubernetes. Use for containerization, production baselines, runtime modes, deployment manifests, readiness, release images, and live deployment verification.
license: Apache-2.0
metadata:
  author: karned-agency
  version: "0.1.0"
---

# Arclith Deploy

Produce one reproducible image and explicit runtime workloads, then verify the live service through its protocol and dependencies. Generation, image build, deployment, and production validation are separate evidence stages.

## Establish the target and current state

Read repository and infrastructure instructions. Determine the requested target: local Docker, Docker Compose, Kubernetes, or another orchestrator. Inspect the project and run:

```bash
arclith-cli version
arclith-cli capabilities --json
arclith-cli status --json
arclith-cli doctor
```

Inspect dependency locks, adapter manifests, `config/`, runtime entrypoints, existing Docker and deployment files, secret references, health/readiness behavior, CI, image registry, and environment overlays. Do not overwrite established deployment conventions with a generic example.

Read [references/deployment-playbook.md](references/deployment-playbook.md) for the selected target.

## Prepare the application first

The service must pass its local functional tests before packaging. Add `probe/server` and `runtime/docker-image` through the current catalog only when missing and required. Preview each mutation with `add-adapter --yes --dry-run` in non-interactive work.

Use the generated Docker contract as the baseline:

- one immutable image containing locked application dependencies;
- runtime selection through the supported `arclith-run` mode or documented environment;
- one primary process per production container;
- separate workloads for API, MCP, agent, or bus consumers when their scaling and failure domains differ;
- no credential or environment-specific configuration baked into the image.

Use `arclith-cli export-config` only for the deployable, non-secret configuration contract. Review the output before turning it into a ConfigMap or equivalent.

## Apply production boundaries

- Inject secrets at runtime through the platform's secret mechanism or an explicit Arclith secrets adapter. Never place secret values in Docker layers, manifests, Git, logs, or generated examples.
- Use durable, shared backends whenever multiple processes or replicas need shared state. Do not deploy memory repositories, caches, idempotency stores, or agent persistence as if they were distributed.
- Configure health for process liveness and readiness for dependency-backed service availability. Keep probes cheap and bounded.
- Set resource requests and limits, a non-root security context where supported, controlled network exposure, and graceful termination.
- Use immutable release tags and preferably image digests. Do not deploy `latest` as evidence of a reproducible release.
- Keep migrations or other persistent-data changes explicit, ordered, backed up, and separately authorized.

## Verify each stage

1. Run project tests and `arclith-cli doctor`.
2. Build the image from the locked dependency state without secrets.
3. Inspect the image metadata and start the exact requested runtime mode locally.
4. Verify health, readiness, and one real application interaction.
5. For Compose, verify dependency readiness, restart behavior, volumes, and network names.
6. For Kubernetes, verify rendered manifests, rollout state, events, pod logs, service endpoints, probes, and a real request through the intended ingress or service path.
7. Confirm the running image digest and effective non-secret configuration match the intended release.

Report live deployment only when the orchestrator and external endpoint were observed. If access stops at build or manifest validation, name that boundary precisely.
