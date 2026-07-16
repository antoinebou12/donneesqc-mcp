# Design: Montréal avis / alertes nearby (`mtl_avis_nearby`)

**Date:** 2026-07-16
**Status:** Approved for implementation
**Sources:**
- https://donnees.montreal.ca/dataset/avis-alertes
- GeoJSON resource: `d249e452-46f5-422f-91ae-898c98eea6cc`
- Viewer: https://montreal.ca/avis-et-alertes

## Goal

Add one purpose-built MCP tool so agents can answer “avis near this address on this date” without inventing locations or scraping montreal.ca HTML.

| MCP tool name | Purpose |
| --- | --- |
| `mtl_avis_nearby` | Alerts active on a date within a radius of an address (or lat/lng) |

## Context

- CSV DataStore (`fc6e5f85-7eba-451c-8243-bdf35c2ab336`) has `titre`, dates, `type`, `lien` but **no coordinates**.
- GeoJSON (~150 KB) has Point and LineString geometries (street segments). Properties do not include Lat/Long columns; coords live in `geometry`.
- City publishes only the last ~12 weeks of alerts.
- Spike (2026-07-16): 800 De La Gauchetière + 2026-07-16 + 800 m → ~22 hits when measuring nearest-vertex distance on LineStrings.

## Non-goals

- Scraping montreal.ca alert HTML pages.
- Borough-only `titre` text search without geometry.
- Historical alerts beyond the GeoJSON window.
- Disk persistence of downloads (in-memory HTTP cache only).

## Architecture

```
helpers/common/config.py       # AVIS_ALERTES_* IDs + GeoJSON URL
helpers/common/http_client.py  # fetch_json (UA, cache)
helpers/mtl/avis_api.py        # fetch GeoJSON, date + radius filter, sort
helpers/mtl/citations.py       # avis_ok(...)
helpers/qc/geo/icherche…       # geocode address → lat/lng

tools/mtl/avis/find_avis_nearby.py
tests/mtl/avis/test_avis_nearby.py
tests/fixtures/mtl/avis_alertes_sample.geojson
```

## Parameters

| Param | Default | Behavior |
| --- | --- | --- |
| `address` | `None` | Geocoded via iCherche when lat/lng not provided |
| `latitude` / `longitude` | `None` | Explicit WGS84 point (override or fallback) |
| `date` | required | `YYYY-MM-DD`; keep if `date_debut ≤ date ≤ date_fin` |
| `radius_m` | `1000` | Clamp 50–5000 |
| `limit` | `20` | Clamp 1–50 |
| `type` | `None` | Optional exact match on alert `type` |

Require a resolvable query point: successful geocode **or** both lat/lng.

## Distance

Min haversine from the query point to any vertex of Point / LineString / MultiLineString (and Polygon exterior if present). Sort ascending by `distance_m`.

## Response schema

```json
{
  "query": {
    "address": "800 rue De La Gauchetière Ouest, Montréal",
    "latitude": 45.501,
    "longitude": -73.5636,
    "date": "2026-07-16",
    "radius_m": 1000,
    "type": null
  },
  "total": 3,
  "alerts": [
    {
      "titre": "...",
      "type": "Circulation et transport",
      "date_debut": "2026-06-25T...",
      "date_fin": "2026-10-23T...",
      "lien": "https://montreal.ca/alertes/...",
      "distance_m": 114.0,
      "geom_type": "LineString",
      "nearest_lat": 45.502,
      "nearest_lon": -73.56327
    }
  ]
}
```

Cite dataset URL + CC BY 4.0 via `avis_ok` / `_meta`.

## Testing

Unit tests with a tiny fixture GeoJSON: date window inclusion/exclusion, LineString nearer than distant Point, radius clamp, missing coords rejected, type filter.
