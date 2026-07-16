# Sécurité

Données Québec MCP est un projet communautaire pour explorer des données ouvertes du Québec. Il n'est pas un service officiel du Gouvernement du Québec et ne doit pas être utilisé pour des démarches citoyennes authentifiées.

## Modèle de menace

### SQL DataStore

Les outils `query_resource_sql` et `query_montreal_sql` transmettent des requêtes au DataStore CKAN. Pour réduire le risque d'injection SQL ou d'écriture accidentelle, les requêtes sont validées avec `sqlglot`, limitées à une seule instruction de lecture (`SELECT` ou `WITH ... SELECT`), plafonnées par `SQL_MAX_LENGTH`, puis filtrées avec une liste de mots-clés interdits en défense en profondeur.

### HTTP sortant

Le serveur interroge des API publiques et quelques pages HTML publiques. Le client HTTP applique des timeouts, retries bornés, respect de `Retry-After` sur 429, rate limiting par hôte (`HTTP_RATE_LIMIT_RPS`, `HTTP_RATE_LIMIT_BURST`) et cache GET TTL en mémoire (`HTTP_CACHE_TTL_SECONDS`, `HTTP_CACHE_MAX_ENTRIES`). Ces limites visent à éviter qu'un agent ou un utilisateur ne transforme le serveur en générateur de trafic excessif vers les portails publics.

### Téléchargements

`download_resource` et les helpers de lecture binaire appliquent `DOWNLOAD_MAX_BYTES` avant et pendant le streaming. Les fichiers trop volumineux sont refusés afin de limiter la mémoire consommée et les coûts réseau.

### Données et citations

Les réponses réussies ajoutent une enveloppe `_meta` avec source, horodatage de récupération et, quand disponible, licence ou identifiants de jeu/ressource. Cette enveloppe aide à citer les données, mais ne remplace pas la vérification humaine de la licence et de la qualité du jeu de données.

## Contrôles automatisés

Le job CI `security` et `make security` exécutent :

- `pip-audit` — vulnérabilités connues des dépendances ;
- `bandit` — analyse statique Python (`helpers/`, `tools/`, `main.py`, `asgi.py`) ;
- `detect-secrets` — détection de clés API / jetons / secrets accidentels (baseline `.secrets.baseline`).

Ne committez jamais de `.env`, clés API, jetons ou données personnelles. Les exemples et tests utilisent uniquement des adresses civiques publiques (ex. Hôtel de Ville de Montréal / 275 rue Notre-Dame Est).

## Signalement

Pour une vulnérabilité exploitable ou sensible, utilisez les GitHub Security Advisories du dépôt si disponibles. À défaut, ouvrez une issue GitHub avec un titre clair, les étapes de reproduction, l'impact attendu et toute mitigation connue. Évitez de publier des secrets, jetons, données personnelles ou payloads destructifs.

Pour un bug non sensible, ouvrez une issue standard.

## Non-objectifs

- Ce projet n'exécute aucune action authentifiée sur des dossiers citoyens, fiscaux, médicaux ou administratifs.
- Ce projet n'est pas un scraper de Québec.ca ni un substitut aux portails officiels.
- Ce projet ne garantit pas l'exactitude, l'exhaustivité, la fraîcheur ou la licence d'un jeu de données tiers.
- Ce projet ne stocke pas durablement les réponses HTTP; le cache est volontairement en mémoire pour rester simple et compatible avec des hébergements serverless.
