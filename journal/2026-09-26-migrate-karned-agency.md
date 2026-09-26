# Migration Arclith vers Karned Agency

## Contexte

Arclith est devenu un framework autonome, publié sur PyPI et utilisé au-delà du
projet Rekipe. Son dépôt, sa documentation et ses implémentations de validation
restaient néanmoins rattachés à l'organisation `karned-rekipe`.

## Décision

- transférer le framework vers `karned-agency/arclith` ;
- publier la documentation sous `https://arclith.karned.bzh/` ;
- renommer le laboratoire `_sample` en `karned-agency/arclith-reference` ;
- transférer le POC documentaire vers
  `karned-agency/arclith-POC-todo` ;
- conserver les noms PyPI `arclith` et `arclith-cli` ;
- enregistrer les deux nouvelles identités OIDC Trusted Publisher avant la
  prochaine publication.

Le dépôt `arclith-reference` reste une implémentation de référence et un banc
d'intégration. Son package Python interne `arclith_sample` est conservé afin de
ne pas transformer une migration de gouvernance en refonte applicative.

## Impacts

- les anciennes URLs GitHub continuent de rediriger tant que les anciens noms
  ne sont pas réutilisés ;
- GitHub Pages utilise désormais un domaine personnalisé indépendant du nom de
  l'organisation ;
- les URLs publiques, les manifests de plugin et les liens générés par la CLI
  pointent vers la nouvelle source de vérité ;
- les empreintes de replay historique de la CLI sont réactualisées uniquement
  pour les fichiers dont les commentaires documentaires changent d'adresse ;
- la prochaine release valide la publication OIDC depuis la nouvelle
  organisation ainsi qu'une installation consommateur sans cache.

## Validation attendue

- `make precommit` ;
- `make coverage` ;
- `make docs` ;
- tests CLI gelés ;
- builds wheel/sdist et `twine check` ;
- CI GitHub, Pages et domaine personnalisé ;
- publication de `arclith` et `arclith-cli` sur PyPI ;
- smoke test consommateur depuis les paquets publics.
