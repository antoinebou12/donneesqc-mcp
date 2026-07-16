---
name: donneesqc-mcp
description: >-
  Maintain and query the Données Québec MCP (CKAN, Montréal, IGO, Adresses
  Québec, OQLF, NosOrigines, Info-pannes Hydro-Québec, murales, Collecte MTL, La bicyclette, Piknic,
  Jazz Fest, neighborhood briefing, evenements publics, calendar week, user context, events soon). Use when editing this repo (tools/, helpers/, Makefile, CI,
  Docker, Smithery, Vercel, README, EXAMPLES.md, docs/, skills/) OR when
  answering Québec/Montréal open-data questions via the donneesqc MCP
  (prefer tools over guessing).
---
# Données Québec MCP

Community (not official Québec government) Streamable HTTP MCP for public open data.
Prefer **uv**, **ruff**, **ty**, **pytest**. Cite source URLs in tool JSON (`source` / `_meta`).

## When to use

1. **Maintain:** editing this repository (tools, helpers, CI, Docker, docs).
2. **Query:** user asks about Québec / Montréal open data and the MCP is available — call tools instead of inventing numbers.

## Query / chat UX

### Tool prefixes

| Prefix | Domain |
| --- | --- |
| `qc_*` | Données Québec CKAN |
| `qc_geo_*` | IGO WFS/WMS, iCherche geocoding |
| `qc_oqlf_*` / `qc_nosorigines_*` | Vitrine / NosOrigines |
| `qc_hydro_*` | Info-pannes Hydro-Québec (état du service) |
| `mtl_*` | donnees.montreal.ca |
| `mtl_murales_*` / `mtl_labicyclette_*` / `mtl_collecte_*` / `mtl_avis_*` | domain APIs |
| `mtl_parcs_*` / `mtl_bixi_*` / `mtl_qualo_*` | parcs, BIXI GBFS, QUALO nearby |
| `mtl_neighborhood_briefing` | Composite quartier (Hydro + avis + QUALO + parcs + BIXI) |
| `mtl_piknic_*` / `mtl_jazzfest_*` | Piknic Électronik / Festival de Jazz |
| `mtl_evenements_*` | Calendrier civique `vmtl-evenements-publics` (DQ CKAN) |
| `mtl_calendar_week` | Agenda semaine (festivals + evenements + avis) |
| `mtl_events_soon` | Événements dans les prochaines heures |
| `common_*` | version, **user context** (date/GPS/IP), tool catalog |

### Typical flows

1. Catalog: `qc_search_datasets` / `mtl_search_datasets` → `qc_list_dataset_resources` → `qc_preview_resource` or SQL.
2. Fast path: `qc_find_and_query` when the question is “find X and show rows”.
3. Dual portal + geo: search both CKAN portals, then `qc_geo_list_layers` (short filters like `MCC`, `velo`; accents/`piste` may miss).
4. Ranked stats: `qc_get_catalog_stats`, `mtl_labicyclette_boroughs` → turn rows into a **markdown table**.
5. **Neighborhood / autour de / briefing:** prefer **`mtl_neighborhood_briefing`** (one call). Fall back to unit tools (`mtl_avis_nearby`, `qc_hydro_outage_status`, `mtl_qualo_nearby`, `mtl_parcs_nearby`, `mtl_bixi_nearby`) for a single domain. Prefer phone GPS (`latitude`/`longitude`) when available; else `address=`. Nearby tools soft-default date to America/Toronto and may use client IP if no GPS/address.
6. **What's on this week / soon:** prefer **`mtl_calendar_week`** for the week; **`mtl_events_soon`** for the next N hours. Call **`common_get_context`** first when the user did not give address/time — pass phone GPS + system timezone when the agent has them. Never rely on MCP host IP.
7. Culture-only: `mtl_evenements_search`. Festival lineups: `mtl_piknic_*` / `mtl_jazzfest_*`. Dated rows include `google_calendar_url`; paste `calendar_ascii` in chat.
8. **NosOrigines:** `qc_nosorigines_search` → `qc_nosorigines_get_person(pid)` → `qc_nosorigines_get_ancestors(pid, generations=1|2)`. Public historical examples only (e.g. François Boucher `781`); treat `Privé` as protected.

### Presentation rules

1. Lead with a 1–2 sentence verdict (counts, key dataset, caveat).
2. Show comparisons and rankings as a **markdown table**.
3. **Do not** render ASCII **bar** charts (La bicyclette ranks → table).
4. **Do** paste day-agenda `calendar_ascii` for schedules; offer `google_calendar_url` links per dated event (do not invent links).
5. **Do not** paste JSON `chart` objects into the reply (La bicyclette may return `chart` for UI clients — ignore it in chat; use the ranked fields as a table).
6. Always cite `_meta.portal_url` or the official dataset URL; note licence when present.
7. Prefer live MCP numbers over stale README snapshots; label snapshots with the month if offline.
8. **Nearby / geo POIs** (murales, avis, parcs, BIXI, QUALO, écocentres, geocode, evenements with address):
   - Render a markdown **link table**: **Dist.** | label | **Maps** (use each row’s `google_maps_url`; do not invent URLs).
   - If `nearest_google_maps_directions_url` (or the nearest item’s `google_maps_directions_url`) is present, add one **Itinéraire** link under the table.
9. **Neighborhood briefing** (EXAMPLES §45):
   - One verdict line from `summary` (Hydro OK / N avis / eau / parcs + BIXI).
   - Fixed section order: **Avis → Hydro → Eau → Parcs → BIXI**.
   - Tables only; **Dist.** as first column; short type labels; include Maps links when present.
   - Source link **under each section**.
   - QUALO: note bathing threshold ~200 UFC/100 mL for coliformes.

### Known data gaps

- IGO **WFS** has no Montréal bike-network layer (~29 layers; MSP/MCC/vigilance). Use MTL/DQ **Réseau cyclable** GeoJSON/SHP (`vmtl-pistes-cyclables` / `pistes-cyclables`).
- IGO **WMS** may expose `convi_velo_glv` (MTQ road bike-friendliness), not municipal paths.
- Provincial Route verte / piste cyclable also appear in RQTT downloads; IGO web service for RQTT may still be “en préparation”.
- iCherche **geocode** omits coordinates unless `geometry=true` (handled in `helpers/qc/geo/icherche_client.py`).
- iCherche **reverse** may return HTTP 400; prefer `address=` for Hydro / nearby tools, or geocode first.
## Stack

| Piece | Detail |
| --- | --- |
| Deps / quality | `uv`, `ruff`, `ty`, `pytest`; `make check` / `make security` |
| Transport | Streamable HTTP only — `POST /mcp`, `GET /health` (no STDIO/SSE) |
| Local / Docker | `main.py` → `mcp.run(transport="streamable-http")` |
| Vercel | `asgi.py` exports `app = mcp.streamable_http_app()`; entrypoint `asgi:app` |
| Tools | Nested under `tools/qc/`, `tools/mtl/`, `tools/common/`; register via `register_all_tools()` |
| Responses | `helpers.common.response.ok(..., source=...)` / `error(...)` |

## Add a tool checklist

Copy and track:

```
- [ ] Env defaults in helpers/common/config.py + .env.example (+ README if user-facing)
- [ ] Prefer helpers/common (ckan_api, ckan_format, portals, tool_call, http_client)
      or helpers/{qc,mtl}/… for domain parsing
- [ ] tools/{qc|mtl|common}/…/<name>.py with @mcp.tool(name="domain_…"); return JSON str
- [ ] Prefer run_tool(...) so ValueError (SQL / validation) reaches the client
- [ ] Import module path in tools/__init__.py → register_all_tools()
- [ ] Examples in tools/common/list_tools_with_examples.py and EXAMPLES.md
- [ ] Unit tests under tests/{qc|mtl|common}/… ; integration fixtures in tests/fixtures/ckan/
- [ ] Cite source via ok(..., source=..., portal_url=...)
- [ ] make check (+ make security if deps/security surface changes)
```

### Tool pattern

```python
from helpers.common.portals import DQ_PORTAL
from helpers.common.response import ok
from helpers.common.tool_call import run_tool
from tools import mcp

@mcp.tool(name="qc_my_tool")
async def my_tool(query: str) -> str:
    """Short docstring; Parameters: listed for the agent."""

    async def _run() -> str:
        data = await some_helper(query)
        return ok({"results": data}, source=DQ_PORTAL.source, portal_url=DQ_PORTAL.base_url)

    return await run_tool("my_tool", _run, generic_error="Request failed.")
```

## Make targets

| Target | Action |
| --- | --- |
| `make sync` | `uv sync --extra dev` |
| `make lint` / `format` / `typecheck` / `test` | quality gates |
| `make check` | lint + format --check + types + tests |
| `make security` | `uv run pip-audit` |
| `make run` | local server |
| `make smithery` | hints for `smithery.yaml` |
| `make docker-up` | build and run compose |

## Rules

- Prefer public APIs (CKAN, iCherche) over HTML; scrapers (OQLF, NosOrigines) must tolerate layout changes.
- Do **not** re-add `genealogiequebec_search_links`.
- NosOrigines fixtures: public/historical names only (e.g. Samuel de Champlain), never personal names. Treat "Privé" as privacy-protected.
- Keep `/health` working for Docker HEALTHCHECK and Vercel.
- No disk persistence — downloads and HTTP caches stay in memory (lower limits when `VERCEL=1`).
- SQL tools: read-only via `sqlglot` validation (ADR 0002); reject writes / multi-statements.
- On Vercel: `stateless_http` + `json_response` auto-on; 5 Mo download default; one-click Deploy badge in README.
- Format with ruff before push: `make format` or `uv run ruff format .`.
- Scope: open-data exploration only — not tax, health, identity, or authenticated citizen portals (ADR 0001).

## Docs map

| Need | Read |
| --- | --- |
| Overview / tools / env | [README.md](../../README.md) |
| Deploy | [DEPLOY.md](../../DEPLOY.md) |
| Security | [SECURITY.md](../../SECURITY.md) |
| Architecture | [docs/architecture/overview.md](../../docs/architecture/overview.md) |
| ADRs | [docs/adr/](../../docs/adr/) |
| Contribute / PR | [CONTRIBUTING.md](../../CONTRIBUTING.md) |
| Examples | [EXAMPLES.md](../../EXAMPLES.md) |
| Smoke EXAMPLES (Cursor) | [.cursor/skills/run-donneesqc-examples/SKILL.md](../../.cursor/skills/run-donneesqc-examples/SKILL.md) |
| Release | [docs/RELEASE.md](../../docs/RELEASE.md) |

For tool catalog, env defaults, and deploy notes, see [reference.md](reference.md).

## Sources

- https://www.donneesquebec.ca/
- https://donnees.montreal.ca/
- https://donnees.montreal.ca/dataset/murales
- https://www.mtlmurales.ca/fr
- https://geoegl.msp.gouv.qc.ca/apis/icherche
- https://vitrinelinguistique.oqlf.gouv.qc.ca/
- https://www.nosorigines.qc.ca/genealogieSearch.aspx?lng=fr
- https://infopannes.solutions.hydroquebec.com
- https://donnees.montreal.ca/dataset/rsma-qualite-de-l-eau-en-rive-qualo
- https://donnees.montreal.ca/dataset/bixi-etat-des-stations
- https://piknicelectronik.com/fr/programmation
- https://montrealjazzfest.com/fr/programmation/horaire
- https://www.donneesquebec.ca/recherche/?q=vmtl-evenements-publics
- https://donnees.montreal.ca/dataset/avis-alertes
