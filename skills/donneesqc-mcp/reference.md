# Données Québec MCP — reference

Condensed from README, DEPLOY, SECURITY, and `docs/`. Read only when you need catalogs or env details.

## Architecture (request path)

```
Agent → POST /mcp → FastMCP → tools/{qc,mtl,common}/*
  → helpers.common.response (ok/error + _meta)
  → helpers.common.ckan_api | helpers.qc.geo | helpers.qc.oqlf | helpers.mtl
  → helpers.common.http_client → public upstream
```

Key modules:

| Path | Role |
| --- | --- |
| `main.py` | Logging, Sentry, Streamable HTTP (local/Docker) |
| `asgi.py` | Vercel ASGI entry (`asgi:app`) |
| `tools/qc/`, `tools/mtl/`, `tools/common/` | `@mcp.tool(name=…)` handlers |
| `helpers/common/ckan_api.py` | CKAN + SQL validation |
| `helpers/common/http_client.py` | Timeout, retry, rate limit, GET cache, download caps |
| `helpers/common/response.py` | `_meta` citation envelope on success |
| `helpers/common/chart_format.py` | Structured bar chart for La bicyclette API (not for chat) |
| `helpers/common/calendar_format.py` | Day-agenda ASCII + Google Calendar TEMPLATE URLs |
| `helpers/common/config.py` | Env defaults |

Diagrams: `docs/architecture/diagrams/` (PlantUML / Mermaid).

## Tool groups

Counts drift; prefer `common_list_tools_with_examples` at runtime.

### `qc` — Données Québec

`qc_search_datasets`, `qc_get_dataset_info`, `qc_list_dataset_resources`, `qc_get_resource_info`, `qc_query_resource_data`, `qc_query_resource_sql`, `qc_list_organizations`, `qc_get_organization_info`, `qc_get_catalog_stats` (totals + top orgs), `qc_download_resource`, `qc_preview_resource`, `qc_find_and_query`, `qc_suggest_sql`, `qc_compare_datasets`, `qc_auto_detect_resource`

### `qc/geo`

`qc_geo_list_layers`, `qc_geo_get_features`, `qc_geo_describe_layer`, `qc_geo_get_map_url`, `qc_geo_geocode`, `qc_geo_reverse_geocode`, `qc_geo_convert_coordinates`, `qc_geo_spatial_intersection`

Geocode / reverse results and WGS84 convert output include `google_maps_url` when coordinates are present.

### `qc/oqlf` / `qc/nosorigines` / `qc/hydro`

`qc_oqlf_search`, `qc_oqlf_get_entry`, `qc_nosorigines_search`, `qc_nosorigines_get_person`, `qc_nosorigines_get_ancestors`, `qc_hydro_outage_status`

NosOrigines person pages: prefer `GenealogieQuebec.aspx?pid=` DOM ids (`#hlnkFather`, `.genealogical_Record_Men`). EXAMPLES §48–49 use public historical **François Boucher** (`pid=781`). Treat display name `Privé` as privacy-protected (do not leak meta keywords).

### `mtl` — catalogue

`mtl_search_datasets`, `mtl_query_data`, `mtl_query_sql`

### `mtl/murales`

`mtl_murales_search`, `mtl_murales_get`, `mtl_murales_nearby`, `mtl_murales_random`, `mtl_murales_facet`

POIs with coords include `google_maps_url`; nearby also returns `nearest_google_maps_directions_url` (and directions on the nearest mural only).

### `mtl/labicyclette`

`mtl_labicyclette_overview`, `mtl_labicyclette_list_counters`, `mtl_labicyclette_get_counter`, `mtl_labicyclette_boroughs` (ranks; may include structured `chart` for UI — use table in chat), `mtl_labicyclette_list_construction`

### `mtl/collecte`

`mtl_collecte_find_waste`, `mtl_collecte_find_ecocentres`, `mtl_collecte_borough_waste_stats`

`mtl_collecte_find_ecocentres` — each site gets `google_maps_url`; payload includes `nearest_google_maps_directions_url`.

### `mtl/avis`

`mtl_avis_nearby` — GeoJSON avis/alertes near address+date (Point/LineString nearest-vertex); Maps pin + nearest directions

### `mtl/parcs` / `mtl/bixi` / `mtl/qualo` / `mtl/neighborhood`

`mtl_parcs_nearby`, `mtl_bixi_nearby`, `mtl_qualo_nearby` — address or lat/lng; iCherche geocode uses `geometry=true`; each hit has `google_maps_url` + `nearest_google_maps_directions_url`

`mtl_neighborhood_briefing` — composite Hydro + avis + QUALO + parcs + BIXI (partial success per section; Maps fields forwarded)

### `mtl/festivals`

`mtl_piknic_search_off`, `mtl_piknic_search`, `mtl_piknic_search_petit`, `mtl_jazzfest_search_free`, `mtl_jazzfest_search_paid` — responses include `calendar_ascii` + per-item `google_calendar_url` when dated

### `mtl/evenements` / `mtl/calendar`

`mtl_evenements_search` — civic calendar `vmtl-evenements-publics` (Données Québec CKAN primary; MTL fallback); address-based `google_maps_url` when emplacement/adresse is present

`mtl_calendar_week` — merge festivals + evenements + avis for a week (`calendar_ascii` day agenda)

`mtl_events_soon` — festivals + civic events in the next N hours (`hours`, optional GPS)

### `common`

`common_get_version`, `common_get_context` (date/time + agent GPS or client IP — never host egress), `common_list_tools_with_examples`

## Environment (common)

| Variable | Default (local) | Notes |
| --- | --- | --- |
| `MCP_HOST` / `MCP_PORT` | `0.0.0.0` / `8000` | Bind address |
| `MCP_STATELESS_HTTP` / `MCP_JSON_RESPONSE` | `false` | Auto `true` on Vercel |
| `DQ_API_URL` | Données Québec CKAN action API | |
| `MTL_API_URL` | donnees.montreal.ca CKAN | |
| `GEO_WFS_URL` / `GEO_WMS_URL` | IGO fcgi | |
| `GEOCODER_URL` | iCherche / Adresses Québec | |
| `VITRINE_BASE_URL` | OQLF Vitrine | |
| `NOSORIGINES_BASE_URL` | NosOrigines | |
| `HYDRO_INFOPANNES_API_URL` | services-bs Info-pannes API | |
| `HYDRO_INFOPANNES_PORTAL_URL` | infopannes.solutions.hydroquebec.com | |
| `PIKNIC_BASE_URL` | piknicelectronik.com | |
| `JAZZFEST_BASE_URL` | montrealjazzfest.com | |
| `DEFAULT_TIMEZONE` | `America/Toronto` | Soft default for « now » |
| `IP_GEO_URL_TEMPLATE` | `https://ipapi.co/{ip}/json/` | Client IP only (`{ip}`) |
| `HTTP_TIMEOUT` | `30.0` | |
| `HTTP_MAX_RETRIES` | `3` | |
| `DOWNLOAD_MAX_BYTES` | 50 MiB (5 MiB on Vercel) | Memory only |
| `SQL_MAX_LENGTH` | `10000` | |
| `HTTP_RATE_LIMIT_RPS` / `BURST` | `5.0` / `10.0` | Per host |
| `HTTP_CACHE_TTL_SECONDS` / `MAX_ENTRIES` | `60` / `256` (30 / 64 on Vercel) | In-memory GET |
| `SENTRY_DSN` | unset | Optional |

Full table: README. Template: `.env.example`.

## Deploy

| Target | Entry | MCP URL |
| --- | --- | --- |
| Vercel (preferred public HTTP) | `asgi:app` | `https://PROJECT.vercel.app/mcp` |
| Docker Compose | `main.py` | `http://127.0.0.1:8000/mcp` |
| Local uv | `uv run python main.py` / `make run` | `http://localhost:8000/mcp` |
| Smithery | `smithery.yaml` | see `make smithery` |

Health: `GET /health` → `{"status":"ok","service":"donneesqc-mcp"}`.
