# Deployment playbook

## Generate the runtime deliberately

Check the live catalog, then preview the required capabilities:

```bash
arclith-cli add-adapter --capability probe --adapter server --yes --dry-run
arclith-cli add-adapter --capability runtime --adapter docker-image --yes --dry-run
```

Apply only missing capabilities after reviewing the plans. Synchronize dependencies and run the project's tests before building.

Documentation: <https://karned-rekipe.github.io/arclith/runtime-docker/>

## Local Docker

Build with the repository's documented command and immutable local tag. Start the selected runtime mode rather than launching an arbitrary module that bypasses Arclith composition. Validate:

- container process remains healthy;
- `/health` and `/ready` have their intended semantics;
- the actual API, MCP, agent, or bus behavior works;
- shutdown reaches the application and adapters cleanly;
- no secret appears in image history, environment dumps, or logs.

## Docker Compose

Use Compose for a reproducible local or small deployment topology. Add dependency health checks and `depends_on` readiness where appropriate, but still make the application tolerate retries and delayed dependencies. Separate durable volumes from disposable container filesystems.

Documentation: <https://karned-rekipe.github.io/arclith/runtime-docker/docker-compose/>

## Kubernetes

Render and review manifests before applying. Use separate Deployments or workloads for independently scaled runtime modes. Provide:

- ConfigMaps for non-secret configuration and Secrets or an external secret system for credentials;
- liveness, readiness, and startup behavior appropriate to the runtime;
- CPU and memory requests and limits;
- non-root and least-privilege security settings supported by the image;
- Services and ingress only for required inbound surfaces;
- persistent external services for shared state;
- immutable image references and a rollback path.

After apply, validate rollout conditions, events, pod identity, effective image digest, logs, probes, and the user-visible endpoint. A green GitOps sync alone does not prove the live application path.

Documentation: <https://karned-rekipe.github.io/arclith/runtime-docker/kubernetes/>

## Production capability review

Review, but do not automatically install, the production baseline for authentication, licensing, shared cache, secrets, probes, observability, and runtime. Each capability must correspond to an accepted requirement and a configured backend.

Documentation: <https://karned-rekipe.github.io/arclith/production/baseline/>
