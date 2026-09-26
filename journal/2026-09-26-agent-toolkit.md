# Kit Portable Pour Agents De Codage

## Contexte

Les utilisateurs d'Arclith devaient jusqu'ici rappeler à chaque agent de codage
les frontières hexagonales, l'usage du catalogue CLI, les règles de déploiement
et les preuves attendues. Cette répétition favorisait les commandes inventées,
les adapters ajoutés implicitement et les validations partielles.

## Décision

Le dépôt distribue un plugin `arclith` conforme à Agent Plugins 1.0. Son cœur
est composé de cinq Agent Skills indépendants du modèle : pilotage général,
transports, agents, déploiement et audit. Des manifestes minces assurent la
compatibilité Codex et Claude Code, avec un marketplace pour chaque client.

La version initiale n'ajoute ni hook ni serveur MCP. La CLI couvre déjà la
découverte, la génération, le dry-run, l'inspection et la validation. Ajouter
un exécutable automatique ou une surface d'outils parallèle augmenterait le
coût et les permissions sans nouveau contrat utile.

## Contrats Préservés

- Le catalogue vivant de `arclith-cli` reste la source de vérité.
- Les skills n'embarquent aucun secret ni choix de provider implicite.
- Les mutations passent par la CLI et ses manifestes lorsque la commande existe.
- Les frontières domaine/application/adapters/infrastructure restent explicites.
- Une génération, un test local et un déploiement live sont rapportés comme des
  niveaux de preuve distincts.
- Les instructions portables ne citent aucun modèle ou client particulier.

## Validation Prévue

- validation des cinq Agent Skills ;
- validation des manifestes portable, Codex et Claude Code ;
- validation des deux marketplaces ;
- tests unitaires des invariants de packaging ;
- build strict de la documentation ;
- smoke test d'un projet généré avec `status` et `doctor`.
