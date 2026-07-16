# Design: Calendar ASCII (day agenda) + Google Calendar links

**Date:** 2026-07-16
**Status:** Approved for implementation planning
**Sources:**
- https://piknicelectronik.com/fr/programmation
- https://montrealjazzfest.com/fr/programmation/horaire
- https://donnees.montreal.ca/dataset/avis-alertes
- https://www.donneesquebec.ca/ (dataset `vmtl-evenements-publics`)
- https://donnees.montreal.ca/ (same civic calendar when present)

## Goal

When tools return event-like rows, each item with usable date/time data MUST include a `google_calendar_url` (Google Calendar TEMPLATE link). Responses also expose a day-agenda `calendar_ascii` string for chat paste. Add a dedicated civic events search tool and a week aggregator; enrich existing festival and avis tools.

## Decisions (locked)

| Topic | Choice |
| --- | --- |
| Scope | Piknic + Jazz Fest + `mtl_avis_nearby` + `vmtl-evenements-publics` |
| Delivery | Shared DTO/adapters + enrich each tool **and** week aggregator |
| Culture tool | `mtl_evenements_search` — primary CKAN = Données Québec; note MTL portal in `_meta` |
| ASCII layout | **C — Day agenda list** (not month grid, not week blocks) |
| Bar charts | Still forbidden in chat; agenda ASCII calendars are allowed |

## Non-goals

- Ticket purchase / checkout.
- Inventing showtimes or caching event payloads to disk.
- Aggregator-only calendar (existing tools must also get GCal when they have dates).
- Replacing markdown tables for rankings (La bicyclette, catalog stats).

## Architecture

```
helpers/common/calendar_format.py
  CalendarItem (kind, start, end, title, place, url, source, all_day)
  google_calendar_url(item) -> str
  calendar_ascii(items) -> str   # day agenda
  attach_calendar(rows, *, list_key) -> adds per-item GCal + response calendar_ascii

helpers/mtl/evenements_api.py     # CKAN search on vmtl-evenements-publics (DQ first, MTL fallback)
helpers/mtl/calendar_adapters.py  # festival event / avis alert / evenement row -> CalendarItem

tools/mtl/evenements/search_evenements.py   # mtl_evenements_search
tools/mtl/calendar/week.py                  # mtl_calendar_week

# Enrich call sites (attach after domain fetch):
tools/mtl/festivals/*.py
tools/mtl/avis/find_avis_nearby.py
```

## Shared item shape

```json
{
  "kind": "festival|avis|evenement",
  "start": "2026-07-19T19:30:00",
  "end": null,
  "all_day": false,
  "title": "Mandragora",
  "place": "SCÈNE FIZZ",
  "url": "https://...",
  "source": "piknic"
}
```

Domain JSON keeps existing field names (`events`, `alerts`, etc.). Calendar fields are **additive**:

- On each dated item: `google_calendar_url` (omit or `null` only if no parseable start date).
- On success payload: `calendar_ascii` (empty string if no dated items).

### Google Calendar URL

`https://calendar.google.com/calendar/render?action=TEMPLATE&text=...&dates=START/END&details=...&location=...`

- Timed: `dates` as `YYYYMMDDTHHMMSS/YYYYMMDDTHHMMSS` (assume America/Toronto wall time when source has local times like `19H30`; document heuristic).
- All-day / date-only / avis windows: all-day form `YYYYMMDD/YYYYMMDD` (end exclusive per Google convention).
- `details` includes source citation URL when known.
- Never invent times: missing time → all-day for that date.

### `calendar_ascii` (layout C)

```
=== Dim 19 juil. 2026 ===
19h30  Piknic · Mandragora @ SCÈNE FIZZ
all-day Avis · Circulation Plateau
10h00  Événement · Festival culturel @ Parc …
```

Group by calendar day (America/Toronto date of `start`). Sort by start within day. Cap lines (e.g. 40) with a trailing `… (+N)` note.

## New tools

### `mtl_evenements_search`

| Param | Default | Behavior |
| --- | --- | --- |
| `query` | `""` | Substring on titre / type / emplacement |
| `date` | `""` | Optional YYYY-MM-DD; keep rows active that day (`date_debut`–`date_fin`) |
| `limit` | `25` | Clamp 1–50 |

- Resolve datastore-active CSV/resource for package `vmtl-evenements-publics` on **DQ_PORTAL** first; if package/resource missing, try **MTL_PORTAL**.
- `_meta`: `source` = portal used; `portal_url` = DQ dataset URL preferred; include `dataset` / `alternate_portal` note that civic calendar is published on Données Québec (and Montréal when used).
- Return `events[]` with titre, type, dates, place, url + calendar fields.

### `mtl_calendar_week`

| Param | Default | Behavior |
| --- | --- | --- |
| `week_start` | `""` | YYYY-MM-DD Monday; empty → current week Monday (America/Toronto) |
| `address` / `lat` / `lon` | optional | Required for avis inclusion |
| `radius_m` | `1000` | Passed to avis |
| `include_festivals` | `true` | Piknic + Jazz categories |
| `include_evenements` | `true` | Civic calendar |
| `include_avis` | `true` | Skip with `warning` if no geo |
| `limit_per_source` | `25` | Clamp |

Returns unified `items[]` (CalendarItem + `google_calendar_url`), `calendar_ascii`, `_meta.sources[]`.

## Enrich existing tools

After successful domain fetch, map rows → CalendarItem → attach GCal + `calendar_ascii`:

- `mtl_piknic_search`, `_off`, `_petit`
- `mtl_jazzfest_search_free`, `_paid`
- `mtl_avis_nearby` (alerts: `date_debut`/`date_fin` → all-day or multi-day window)

Do not change existing error strings or core schemas beyond additive fields.

## Error handling

| Case | Behavior |
| --- | --- |
| No parseable date on a row | Item kept; `google_calendar_url` = `null`; excluded from ASCII |
| Invalid `date` / `week_start` | `ValueError` → client error via `run_tool` |
| DQ package missing, MTL works | OK with `_meta` note |
| Both portals fail evenements | error / empty + warning (same pattern as festivals) |
| Aggregator avis without geo | Omit avis; `warning` explaining need for address/coords |

## Tests

- Unit: `calendar_format` (GCal encoding, all-day vs timed, ASCII grouping, omit undated).
- Adapters: one festival fixture row, one avis fixture, one evenement fixture → CalendarItem.
- Tools: mock helpers; assert `google_calendar_url` present when dated; `_meta.portal_url` for evenements.
- No live network in default pytest.

## Docs / skill

Update:

- `skills/donneesqc-mcp/SKILL.md` — allow day-agenda ASCII; document `google_calendar_url`; list `mtl_evenements_*` / `mtl_calendar_week`; keep “no ASCII bar charts”.
- `skills/donneesqc-mcp/reference.md`, `EXAMPLES.md`, `README.md`, `tools/common/list_tools_with_examples.py`, `tools/__init__.py` instructions.

## Chat UX (skill)

1. Prefer pasting `calendar_ascii` for “what’s on” answers.
2. Offer `google_calendar_url` links for individual events (do not invent links).
3. Still use markdown tables for rankings; never dump La bicyclette `chart` JSON.
