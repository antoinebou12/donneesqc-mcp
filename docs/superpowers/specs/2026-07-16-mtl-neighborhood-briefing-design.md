# Design: Montréal neighborhood briefing (`mtl_neighborhood_briefing`)

**Date:** 2026-07-16
**Status:** Approved for implementation
**Sources:**
- Avis: https://donnees.montreal.ca/dataset/avis-alertes · https://montreal.ca/avis-et-alertes
- Hydro: https://infopannes.solutions.hydroquebec.com
- QUALO: https://donnees.montreal.ca/dataset/rsma-qualite-de-l-eau-en-rive-qualo
- Parcs: https://donnees.montreal.ca/dataset/grands-parcs-parcs-d-arrondissements-et-espaces-publics
- BIXI: https://donnees.montreal.ca/dataset/bixi-etat-des-stations · https://gbfs.velobixi.com/gbfs/gbfs.json

## Goal

One composite MCP tool so agents can answer “what’s going on around this Montréal address?” in a single call: Hydro service status, avis/alertes, shore water quality (QUALO), nearby parks, and BIXI availability.

| MCP tool name | Purpose |
| --- | --- |
| `mtl_neighborhood_briefing` | Fan-out briefing for an address or lat/lng |

## Inputs

| Param | Default | Behavior |
| --- | --- | --- |
| `address` | `None` | Geocoded when lat/lng not both provided |
| `latitude` / `longitude` | `None` | Explicit WGS84 (coords win over geocode) |
| `date` | today (America/Toronto) | `YYYY-MM-DD` for avis window |
| `avis_radius_m` | `1000` | Clamp 50–5000 |
| `parks_radius_m` | `300` | Clamp 50–5000 |
| `bixi_radius_m` | `400` | Clamp 50–5000 |
| `qualo_radius_m` | `1500` | Clamp 50–5000 |
| `limit` | `10` | Max items per list section (1–50) |

Require a resolvable query point: successful geocode **or** both lat/lng.

## Flow

1. Resolve query lat/lng (avis-style: coords preferred).
2. Resolve Hydro civic fields (`address` → forward, else reverse from coords).
3. `asyncio.gather` (partial success):
   - Hydro Info-pannes
   - `avis_api.list_nearby`
   - QUALO DataStore + haversine (latest sample per station)
   - Parks GeoJSON + nearest-vertex distance
   - BIXI GBFS information + status
4. Build `summary` booleans/counts; return `ok(...)` with per-section `source` URLs.
5. Section exceptions become `{ "error": "..." }` — do not fail the whole tool.

## Architecture

```
helpers/mtl/geo.py                 # shared haversine + GeoJSON distance
helpers/common/config.py           # BIXI / QUALO / parks IDs
helpers/mtl/bixi_api.py
helpers/mtl/parks_api.py
helpers/mtl/qualo_api.py
helpers/mtl/neighborhood_api.py    # fan-out + summary
helpers/mtl/citations.py           # neighborhood_ok
tools/mtl/neighborhood/briefing.py
tests/mtl/neighborhood/
tests/fixtures/mtl/
```

## Response schema

See plan: `query`, `summary`, `hydro`, `avis`, `water_quality`, `parks`, `bixi`.

## Chat presentation (agents)

1. One verdict sentence from `summary`.
2. Sections in order: Avis → Hydro → Eau → Parcs → BIXI.
3. Markdown tables only; Dist. first column; source under each section.
4. QUALO bathing note: ~200 UFC/100 mL.

## Non-goals

- Standalone MCP tools for BIXI / parks / QUALO alone.
- Scraping montreal.ca HTML.
- Collecte MTL in v1.
- Disk persistence of GeoJSON/GBFS.
