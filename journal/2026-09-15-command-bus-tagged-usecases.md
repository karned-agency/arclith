# Command Bus — usecases groupés via `@command` (breaking change)

## Contexte

`CommandDispatcher`/`CommandHandler` imposaient une classe dédiée par commande. Pour un projet qui
grandit vite (nombreuses commandes CRUD par ressource), ce ratio 1 classe = 1 commande multiplie les
fichiers et éclate la logique d'un même usecase entre plusieurs classes.

## Décisions

- ajouter `command(name)`, un décorateur qui tague une méthode (`(payload, headers) -> Awaitable`)
  avec le nom de commande qu'elle traite ; nom vide → `ValueError` immédiat (déclaration
  obligatoire) ;
- ajouter `CommandDispatcher.register_handlers(obj)` qui scanne n'importe quel objet
  (`inspect.getmembers(obj, predicate=inspect.ismethod)`) et enregistre chaque méthode taguée —
  aucune classe parente requise, duck-typing pur ;
- **supprimer le port `CommandHandler`** (ABC, une classe par commande) : la lib est encore en alpha
  `0.x`, pas de période de dépréciation. `CommandDispatcher.register(command_type, method)` remplace
  `register(handler)` ;
- `CommandDispatcher.__init__(handlers=[...])` appelle désormais `register_handlers()` pour chaque
  objet de la liste ;
- rejeté en cours de conception : classe marqueur (`UseCases`), registre global par décorateur de
  classe, wrapper `command_dispatcher_from_instances()` — tous ajoutaient de la surface d'API ou du
  couplage sans bénéfice net face au duck-typing simple ;
- mise à jour du générateur `arclith-cli` (`binding_rendering.py::_rabbitmq`) pour émettre le nouveau
  pattern (`class Handler` avec méthode `@command(...)`, `dispatcher.register_handlers(Handler(...))`).

## Impact

Ajouter une commande à un usecase existant devient : une méthode + `@command("...")`, sans nouveau
fichier ni nouvelle classe à câbler ailleurs. Un usecase peut exposer plusieurs commandes
(`create`/`update`/`read`...) dans une seule classe.

**Breaking change** : tout code consommateur utilisant `class XCommandHandler(CommandHandler):
command_type = "..."` doit migrer vers une méthode `@command("...")` sur sa classe usecase. Le CLI
(`expose-usecase --via rabbitmq`) génère déjà le nouveau pattern pour les nouveaux projets.

## Documentation

- `docs/command-bus.md` — section "Handler" réécrite pour ne présenter que `@command`.
- `docs/capabilities/command-bus.md`, `docs/deep-dives/bus.md` — exemples mis à jour.
- `docs/decisions.md` (ADR-012) — addendum documentant le retrait de `CommandHandler`.
- `CHANGELOG.md` — entrée `[Unreleased] / Changed — BREAKING`.

## Validation

```bash
uv run pytest tests/units/application/test_command_bus.py \
  tests/units/adapters/bidirectional/rabbitmq/test_command_bus.py \
  tests/units/test_arclith_command_bus.py tests/units/test_init.py
# 37 passed

cd cli && uv run pytest tests/test_usecase_binding.py tests/test_add_adapter.py
# 199 passed
```



