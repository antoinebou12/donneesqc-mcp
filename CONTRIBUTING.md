# Contribuer

Merci de contribuer à Données Québec MCP. Le projet est communautaire, non officiel, et vise l'accès en lecture seule aux données ouvertes.

## Démarrage

```bash
git clone https://github.com/Stefen-Taime/donneesqc-mcp.git
cd donneesqc-mcp
uv sync --extra dev
cp .env.example .env
```

Dans Cursor, VS Code ou GitHub Codespaces, utilisez **Open in Dev Container** si une configuration Dev Container est disponible dans votre environnement ou votre fork.

## Boucle de développement

```bash
make check
make test
make security
```

`make check` exécute Ruff, le formatage en mode vérification, ty et pytest. `make security` lance `pip-audit`.

Installez les hooks locaux si vous préparez des commits :

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

## Règles de contribution

- 1 fonctionnalité = 1 PR.
- Gardez les changements petits, testables et alignés avec les helpers existants.
- Préférez les API publiques et les endpoints open data aux scrapers HTML.
- Ajoutez ou ajustez les tests quand vous modifiez un outil, un helper partagé ou une règle de sécurité.
- Citez les sources dans les réponses d'outils via `helpers.common.response.ok(...)` et l'enveloppe `_meta`.
- Vérifiez la licence de chaque jeu de données avant de publier des exemples ou résultats réutilisables.

## Pull Requests

Avant d'ouvrir une PR :

- exécutez `make check`, `make test` et `make security`;
- documentez les nouvelles variables d'environnement dans `.env.example` et `README.md`;
- mettez à jour `EXAMPLES.md`, `docs/` ou les ADRs si le comportement utilisateur change;
- évitez les fichiers générés locaux comme `.venv`, `.pytest_cache` et `.ruff_cache`.
