# Déploiement — Données Québec MCP

Guide pour héberger votre propre instance. Aucune clé API n’est requise pour un déploiement de base (sources publiques).

**Stockage :** le serveur n’écrit pas sur disque. Téléchargements et caches HTTP restent **en mémoire** (limites plus basses sur Vercel).

---

## 1. Vercel (recommandé pour HTTP public)

One-click :

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FStefen-Taime%2Fdonneesqc-mcp&project-name=donneesqc-mcp&repository-name=donneesqc-mcp)

### Étapes

1. Cliquez sur **Deploy** et liez un compte GitHub / GitLab / Bitbucket.
2. Laissez Vercel cloner le dépôt et lancer le build Python (`asgi:app`).
3. Attendez le déploiement, puis ouvrez `https://<votre-projet>.vercel.app/health` — réponse attendue : `{"status":"ok",...}`.
4. Pointez votre client MCP vers `https://<votre-projet>.vercel.app/mcp`.

### Comportement serverless

- `VERCEL=1` active automatiquement `stateless_http` et `json_response` (pas d’affinité de session).
- Téléchargements plafonnés à **5 Mo** par défaut ; cache GET limité (TTL 30 s, 64 entrées).
- Durée max de fonction : **60 s** (`vercel.json`).

Variables optionnelles dans le tableau de bord Vercel : `SENTRY_DSN`, `DOWNLOAD_MAX_BYTES`, URLs CKAN / IGO si vous voulez surcharger les défauts.

CLI locale :

```bash
npx vercel          # preview
npx vercel --prod   # production
```

---

## 2. Docker Compose

```bash
git clone https://github.com/Stefen-Taime/donneesqc-mcp.git
cd donneesqc-mcp
docker compose up -d
curl http://127.0.0.1:8000/health
```

Endpoint MCP : `http://127.0.0.1:8000/mcp`.

---

## 3. Développement local (`uv`)

```bash
uv sync --extra dev
cp .env.example .env
uv run python main.py
```

Ou : `make sync` puis `make run`.

---

## 4. Smithery

Voir [`smithery.yaml`](smithery.yaml) et `make smithery` pour les indices de publication sur [Smithery](https://smithery.ai).

---

## Contraintes

| Point | Détail |
|---|---|
| Transport | **Streamable HTTP uniquement** (`POST /mcp`) — pas de STDIO / SSE legacy |
| Santé | `GET /health` |
| Vercel | Mode **stateless** ; pas de stockage local durable |
| Téléchargements | Mémoire seule ; plafond 50 Mo (local) / 5 Mo (Vercel) |
| Contenu payant | Ne pas scrapers d’archives payantes |

---

## English (short)

Deploy your own instance with the **Deploy** button above, then use `https://<project>.vercel.app/mcp`. No disk writes — RAM-only caches/downloads. Docker and local `uv` remain supported for long-lived processes. See the French sections for full steps.
