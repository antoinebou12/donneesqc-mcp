# Design: Hydro-Québec Info-pannes outage status (`qc_hydro_outage_status`)

**Date:** 2026-07-16
**Status:** Approved for implementation
**Sources:**
- Portal: https://infopannes.solutions.hydroquebec.com
- API base: https://services-bs.solutions.hydroquebec.com/pan/web
- Geocoding: Adresses Québec / iCherche (`GEOCODER_URL`)

## Goal

One MCP tool so agents can answer “is power out at this address?” using the same public Info-pannes flow as the SPA: resolve civic fields → `lieux-conso` → `lieux-conso/etats/{id}`.

| MCP tool name | Purpose |
| --- | --- |
| `qc_hydro_outage_status` | Outage / service status for an address or lat/lng |

## Inputs

| Param | Rule |
| --- | --- |
| `address` | Optional freeform string |
| `latitude` / `longitude` | Optional WGS84 pair |
| `appartement` | Optional unit number (`numeroAppartement`) |

Require exactly one of: non-empty `address`, or both coordinates.

## Flow

1. Resolve civic fields via Adresses Québec (`/geocode` or `/reverse`).
2. Normalize postal code to `A1A 1A1`.
3. `GET /api/v1/lieux-conso?…&hqToken={uuid4}` (client correlation ID, not a secret).
4. `GET /api/v1/lieux-conso/etats/{id}` (comma-separated for multi-unit).
5. Map `etat`: `A` = alimenté, `N` = non alimenté.

## Architecture

```
helpers/common/config.py          # HYDRO_INFOPANNES_* URLs
helpers/qc/hydro/address_resolve.py
helpers/qc/hydro/infopannes_api.py
tools/qc/hydro/outage_status.py
tests/qc/hydro/test_infopannes.py
```

## Non-goals

- Official BIS open-data map markers (region-level) — deferred.
- Persisting `lieuConsommation` IDs to disk.
- Live HQ calls in CI (mocked HTTP only).
- Authenticated Hydro customer account APIs.

## Privacy / fixtures

Tests and examples use public civic addresses (e.g. Place Ville-Marie). Do not use personal residence addresses or personal genealogy names in fixtures.

## Disclaimer

Responses include the standard community `_meta.disclaimer` plus a payload `note` that Info-pannes data is approximate and this wrapper is not affiliated with Hydro-Québec.
