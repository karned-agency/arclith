# Capability Logger

Le CLI crée dès l'installation tous les fichiers et packages du [blueprint complet
de cette capability](../deep-dives/adapter-blueprints.md), avec des repères pour les
développeurs et les IA. Les fichiers existants sont préservés lors d'une relance.

Logger applicatif partagé par les use cases et les adapters.

## Objectif

Fournir un port de logging commun pour les use cases, adapters et runners, avec
des métadonnées exploitables par l'observabilité.

## Adapter

| Adapter | Usage |
|---|---|
| `console` | JSON natif Loguru vers `stderr`, avec classe appelante et contexte OpenTelemetry si actif |

## Commande

```bash
arclith-cli add-adapter --capability logger --adapter console --yes
```

## Configuration

```yaml
# config/adapters/adapters.yaml
logger: console
```

## Utiliser

```python
logger = arclith.logger
logger.info("todo created", todo_uuid=str(todo.uuid))
```

## Composant Émetteur

Les appels `log(level, message, **metadata)`, `info()`, `debug()`, etc. restent
inchangés. Le logger détecte automatiquement la première classe appelante qui
n'est pas une instance du port `Logger`, en remontant la pile Python.
Le champ `text` du JSON contient la ligne formatée :

```text
2026-11-05 17:04:30 | 💬 INFO     | CreateTodoUseCase | todo created | {'todo_uuid': '...'}
```

`component` identifie la classe émettrice, pas le nom du service déployé.
Un wrapper intermédiaire possédant un `self` peut être retenu à la place du
use case ; sans instance détectable, la valeur est `Global`.
Pour fournir une origine explicite, passer une chaîne non vide :

```python
logger.info("worker started", component="external.worker")
```

Les logs interceptés depuis Uvicorn et `watchfiles` utilisent le nom du logger
source, par exemple `uvicorn.access`, plutôt que la classe du handler.
Le composant est lié dans `extra.component` de Loguru et transmis comme
attribut `component` aux records OpenTelemetry lorsque l'export est activé.
Les autres métadonnées et la priorité du contexte réel de corrélation sont
préservées.

## JSON Natif Et Recherche Loki

Le sink console utilise `serialize=True` et `colorize=False` : chaque événement
est un objet JSON natif Loguru sur une seule ligne physique, sans couleurs ANSI.
Tous les niveaux restent envoyés vers `stderr`. Les retours à la ligne des
messages sont échappés dans le JSON et les métadonnées imbriquées sont conservées.
Les objets non directement sérialisables, comme les UUID, sont convertis en
chaînes par Loguru.

Le JSON contient `text` (la ligne formatée) et `record` (le record structuré
complet : niveau, message, date, origine, processus, thread et métadonnées).
Voici un extrait simplifié :

```json
{
  "text": "2026-11-05 17:04:30 | 💬 INFO     | CreateTodoUseCase | todo created | {'system_uuid': 'abc-123'}\n",
  "record": {
    "level": {"name": "INFO", "no": 20, "icon": "ℹ️"},
    "message": "todo created",
    "extra": {
      "component": "CreateTodoUseCase",
      "level_emoji": "💬",
      "meta": {"system_uuid": "abc-123"}
    }
  }
}
```

Dans Grafana/Loki, adapter le sélecteur aux labels de la collecte et extraire
explicitement les champs souhaités :

```logql
{app="my-service"}
| json level="record.level.name",
       component="record.extra.component",
       system_uuid="record.extra.meta.system_uuid",
       log_message="record.message"
| level=~"INFO|DEBUG"
| system_uuid="abc-123"
```

Pour afficher seulement le message après filtrage, ajouter
`| line_format "{{.log_message}}"`.
Le JSON facilite les filtres, mais ne crée pas d'index sur chaque champ.
Limiter la période et sélectionner les labels de service/environnement avant
le parsing ; ne pas transformer les UUID en labels Loki indexés.

L'API publique, la corrélation et les records OTLP ne changent pas :
OpenTelemetry reçoit le message et les attributs structurés, pas le JSON console.
La sortie console remplace l'ancien texte brut ; les collecteurs et scripts
qui parseaient ce texte doivent lire le JSON natif.

## Règles

- Les use cases reçoivent un logger injecté.
- Ne pas utiliser `print()` pour les logs applicatifs.
- Ne jamais logger de token, mot de passe ou payload sensible.
- Ajouter `correlation_id`, `tenant_id` ou `trace_id` quand disponibles.
- Laisser Uvicorn passer par l'interception Arclith.

## Validation

```bash
uv run pytest
```

## Suite

Lire [observability](observability.md) pour corréler logs et traces.
