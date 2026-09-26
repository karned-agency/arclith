# Arclith

Framework Python 3.13 pour construire des microservices hexagonaux avec domaine, ports, use cases,
adapters, FastAPI, FastMCP, bus, canaux conversationnels, agents, configuration, observabilité et
runtime Docker.

Pour construire puis piloter un projet sans quitter le terminal, lancez
`uvx --from arclith-cli arclith-cli` sans argument : le cockpit plein écran
guide la création, inspecte le projet et démarre ses runtimes avec leurs logs.
Les commandes directes restent disponibles pour les scripts et la CI.

```bash
uvx --from arclith-cli arclith-cli init my-service --dir .
cd my-service
uv sync
uvx --from arclith-cli arclith-cli run api
curl -fsS http://127.0.0.1:9000/health
```

Documentation : [arclith.karned.bzh](https://arclith.karned.bzh/)

Pour installer une fois les workflows Arclith dans Codex, Claude Code ou un
client compatible Agent Skills, utiliser le
[kit Arclith pour agents de codage](https://arclith.karned.bzh/agent-toolkit/).

Liens utiles :
[issues](https://github.com/karned-agency/arclith/issues),
[releases](https://github.com/karned-agency/arclith/releases),
[arclith PyPI](https://pypi.org/project/arclith/),
[arclith-cli PyPI](https://pypi.org/project/arclith-cli/).

Licence Apache 2.0.
