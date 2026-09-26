# Kit Arclith Pour Agents De Codage

Le plugin `arclith` permet d'installer une seule fois les règles de travail
Arclith dans un agent de codage. Il ne dépend pas d'un modèle particulier : le
cœur suit les standards ouverts [Agent Skills](https://agentskills.io/) et
[Agent Plugins](https://agent-plugins.org/).

Le même paquet fournit cinq workflows spécialisés :

| Skill | Usage |
|---|---|
| `arclith` | initialiser ou faire évoluer un projet et choisir le bon parcours |
| `arclith-api` | créer une API REST, des tools MCP ou un consumer RabbitMQ |
| `arclith-agent` | créer un agent LangGraph, ses tools, son LLM et sa persistance |
| `arclith-deploy` | générer et valider Docker, Compose ou Kubernetes |
| `arclith-audit` | auditer un projet existant sans le modifier par défaut |

```text
plugin arclith
├── skills/                 # noyau portable, indépendant du modèle
├── plugin.json             # manifeste Agent Plugins 1.0
├── .codex-plugin/          # compatibilité Codex
└── .claude-plugin/         # compatibilité Claude Code
```

## Ce Que Le Kit Impose

Chaque workflow demande à l'agent de :

1. lire les règles du dépôt et préserver les changements existants ;
2. interroger `arclith-cli capabilities --json` et `blueprints --json` au lieu
   d'inventer une capability ou un paramètre ;
3. inspecter `status --json`, `doctor`, la recette et les manifestes lorsqu'un
   projet existe déjà ;
4. utiliser les dry-runs de la CLI avant les mutations non triviales ;
5. maintenir les frontières `domain`, `application`, `adapters` et
   `infrastructure` ;
6. vérifier le résultat par les tests et le protocole réellement touché ;
7. distinguer ce qui est généré, testé localement, déployé et vérifié en
   production.

Le catalogue de la CLI reste la source de vérité. Une mise à jour d'Arclith peut
donc ajouter un adapter sans qu'il soit nécessaire de recopier tout le catalogue
dans les prompts du plugin.

## Installer Dans Codex

Ajouter le dépôt comme marketplace, puis installer le plugin :

```bash
codex plugin marketplace add karned-agency/arclith --ref main
codex plugin add arclith@arclith
```

Démarrer une nouvelle tâche après l'installation. Le plugin peut être invoqué
explicitement, par exemple :

```text
Utilise $arclith pour initialiser un service de facturation.
Utilise $arclith-api pour exposer la création d'une facture en REST.
Utilise $arclith-audit pour vérifier ce projet sans le modifier.
```

Codex peut aussi sélectionner automatiquement un skill lorsque la demande
correspond à sa description.

## Installer Dans Claude Code

Le même dépôt est une marketplace Claude Code :

```bash
claude plugin marketplace add karned-agency/arclith
claude plugin install arclith@arclith
```

Redémarrer ou recharger les plugins, puis invoquer un workflow avec le préfixe
du plugin :

```text
/arclith:arclith Initialise un service de facturation.
/arclith:arclith-agent Ajoute un agent qui utilise les use cases existants.
/arclith:arclith-deploy Prépare et vérifie le déploiement Kubernetes.
```

## Autres Agents Compatibles

Un client compatible Agent Plugins 1.0 peut charger directement le dossier
`plugins/arclith`. Un client qui comprend Agent Skills mais pas encore Agent
Plugins peut installer séparément les sous-dossiers de
`plugins/arclith/skills/` dans son répertoire de skills.

Pour un agent sans support de ces standards, fournir le `SKILL.md` correspondant
comme instruction de projet. Cette solution de repli conserve les règles de
travail, mais perd la découverte automatique, les métadonnées et les mises à
jour groupées du plugin.

## Pourquoi Il N'y A Ni Hook Ni Serveur MCP

La première version est volontairement un plugin de skills uniquement :

- `arclith-cli` fournit déjà les opérations déterministes de découverte,
  génération, inspection et validation ;
- un serveur MCP dupliquerait cette surface sans apporter de donnée distante ni
  de contrôle d'accès supplémentaire ;
- un hook exécuté automatiquement augmenterait les permissions et le coût de
  chaque session, alors que `status`, `doctor` et les smoke tests doivent être
  choisis selon le changement effectué.

Un hook ou un MCP devra être ajouté uniquement s'il comble un manque observable
que la CLI et les skills ne peuvent pas traiter proprement.

## Développer Et Valider Le Plugin

Le paquet source se trouve dans `plugins/arclith`. Toute évolution doit garder
les trois manifestes au même nom et à la même version, conserver des
instructions neutres vis-à-vis du modèle, et valider les cinq skills.

```bash
claude plugin validate plugins/arclith
skills-ref validate plugins/arclith/skills/arclith
uv run --frozen pytest -q tests/units/test_agent_plugin_package.py
```

Répéter `skills-ref validate` pour chacun des cinq sous-dossiers. Les tests du
dépôt contrôlent également les manifestes, les marketplaces, le frontmatter et
l'absence de contenu spécifique à Codex ou Claude dans le cœur portable.
