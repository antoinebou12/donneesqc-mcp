# Design: Montréal festival tools (Piknic + Jazz Fest)

**Date:** 2026-07-16
**Status:** Approved for implementation planning
**Sources:**
- https://piknicelectronik.com/fr/programmation
- https://montrealjazzfest.com/fr (program schedule Free / Paid)

## Goal

Add five purpose-built MCP tools so agents can list or search public festival lineups without inventing showtimes:

| MCP tool name | Category |
| --- | --- |
| `mtl_piknic_search_off` | OfF Piknic |
| `mtl_piknic_search` | Piknic (main) |
| `mtl_piknic_search_petit` | Petit Piknic |
| `mtl_jazzfest_search_free` | Jazz Fest — free |
| `mtl_jazzfest_search_paid` | Jazz Fest — paid |

List all matching events when `query` is empty; filter by artist/title when `query` is set. Optional `date` filter supports questions like “Piknic this Sunday”.

## Context

- Repo pattern: HTML scrapers in `helpers/…`, thin `@mcp.tool` wrappers, `ok`/`error` with `_meta.source` / `portal_url`.
- Layout (current): domain packages under `helpers/mtl/`, `helpers/qc/`, `helpers/common/`; tools under `tools/mtl/`, `tools/qc/` with namespaced MCP names (e.g. `qc_oqlf_search`).
- Spike (2026-07-16): `httpx` + BeautifulSoup text-line parse of Piknic programmation successfully extracted Sun Jul 19 Piknic + Petit Piknic cards (Mandragora, etc.).

## Non-goals

- Ticket purchase / checkout automation.
- Unofficial mobile-app private APIs as primary source.
- Re-adding removed genealogy link tools.
- Inventing or caching showtimes to disk (in-memory HTTP cache only).

## Architecture

```
helpers/common/config.py          # PIKNIC_BASE_URL, JAZZFEST_BASE_URL
helpers/common/http_client.py     # fetch_text (cache, timeout, UA)
helpers/mtl/piknic_api.py         # fetch + parse + filter by experience
helpers/mtl/jazzfest_api.py       # fetch + parse + filter free|paid

tools/mtl/festivals/
  search_piknic_off.py
  search_piknic.py
  search_piknic_petit.py
  search_jazzfest_free.py
  search_jazzfest_paid.py

tests/test_festivals.py
tests/fixtures/piknic_programmation.html
tests/fixtures/jazzfest_program.html
```

Register imports in `tools/__init__.py` → `register_all_tools()`, and keep any package `__init__` re-exports consistent with existing MTL tools.

## Parameters (all five tools)

| Param | Default | Behavior |
| --- | --- | --- |
| `query` | `""` | Empty → list; non-empty → case-insensitive substring on artist name / title / stage |
| `date` | `""` | Optional `YYYY-MM-DD` or parseable day label match; empty → no date filter |
| `limit` | `25` | Clamp to 1–50 |

## Response schema

Shared event object:

```json
{
  "date": "2026-07-19",
  "date_label": "Sun, Jul 19",
  "category": "piknic|off|petit|free|paid",
  "venue_or_stage": "SCÈNE FIZZ",
  "artists": [{"name": "Mandragora", "time": "19H30"}],
  "title": null,
  "ticket_url": "https://...",
  "url": "https://..."
}
```

Success payload:

```json
{
  "query": "",
  "date": "2026-07-19",
  "category": "piknic",
  "count": 1,
  "events": [],
  "warning": null,
  "_meta": {
    "source": "piknic",
    "portal_url": "https://piknicelectronik.com/fr/programmation",
    "retrieved_at": "...",
    "disclaimer": "..."
  }
}
```

- `source` values: `"piknic"` or `"jazzfest"`.
- Optional fields missing from HTML → `null`, never invented.

**Flattening:** one event object per `(date, experience, stage)` with that stage’s artists list. Petit / single-stage days produce one event.

## Scraping strategy

### Piknic

1. `GET` `{PIKNIC_BASE_URL}/fr/programmation` via `fetch_text`.
2. Parse with BeautifulSoup; primary strategy = normalized text lines (proven in spike):
   - Date lines: `Sun, Jul 19`
   - Experience lines: `OfF PIKNIC` | `Piknic` | `PETIT PIKNIC`
   - Stage lines: start with `SCÈNE` / `SCENE` / `Scène`
   - Artist + next line time `19H30`
   - Skip chrome: `Billets`, `Achète tes billets`, month tabs
3. Map experience → tool category (`off` / `piknic` / `petit`).
4. Best-effort absolute `ticket_url` from nearby anchors when present.
5. Normalize `date` to ISO when year known (festival season year from page or current UTC year heuristic documented in code).

### Jazz Fest

1. `GET` FR program schedule URL (config default pointing at Free/Paid program page under `montrealjazzfest.com/fr`).
2. Parse Free vs Paid using on-site distinction (section headings, filters, or attributes in HTML).
3. Extract artist, date/time, venue, ticket URL when paid.
4. First ship: static HTML only. If HTML is empty (JS shell), return `events: []` + `warning` explaining possible client-rendered page; document follow-up (embedded JSON discovery) out of scope for v1.

## Error handling

| Case | Behavior |
| --- | --- |
| HTTP / timeout / network | `error("Impossible de joindre Piknic Électronik.")` / Jazz Fest equivalent |
| HTTP OK, zero parseable events | `ok` with `events: []`, `count: 0`, `warning` (layout change or off-season) |
| Bad / empty query | Not an error; empty list after filter |
| Invalid limit | Clamp 1–50 |
| Invalid date format | `error("Date invalide (utilisez YYYY-MM-DD).")` |

Never invent showtimes. Always cite portal via `ok(..., source=..., portal_url=...)`.

## Config / env

In `helpers/common/config.py` + `.env.example`:

```text
PIKNIC_BASE_URL=https://piknicelectronik.com
JAZZFEST_BASE_URL=https://montrealjazzfest.com
```

Program paths as module constants (not env):

- Piknic: `/fr/programmation` (verified).
- Jazz Fest: set `JAZZFEST_PROGRAM_PATH` after verifying the FR schedule page that exposes Free / Paid markup (candidate: `/fr/programmation` or `/fr/program/horaire` — confirm against live HTML before locking the constant).

## Tests

`tests/test_festivals.py` + fixtures:

1. **Piknic fixture** with OfF / Piknic / Petit cards → each filter returns only its category; `query="Mandragora"` hits Piknic only.
2. **Piknic date filter** `date="2026-07-19"` returns Sunday cards only.
3. **Jazz Fest fixture** free + paid rows → no cross-contamination.
4. **Empty HTML** → `events: []` + warning.
5. **Tool wrappers** with AsyncMock helpers → `_meta.source` / `portal_url` present; HTTP failure → `error`.

No live network in CI.

## Docs

- README: new “Festivals Montréal” section (5 tools); bump tool count.
- `EXAMPLES.md`: one example per tool (list + search + Sunday date).
- `tools/__init__.py` MCP `instructions`: mention Piknic + Jazz Fest free/paid.
- `list_tools_with_examples.py` examples.
- Skill/reference update only if maintaining tool catalog there.

## Implementation notes

- Prefer `helpers.common.http_client.fetch_text` and `helpers.common.response.ok` / `error`.
- Mirror OQLF/NosOrigines: logic in helpers, tools only validate/clamp/call/wrap.
- French user-facing error strings, consistent with existing tools.
- ruff / ty / pytest via `make check` before done.

## Open follow-ups (explicitly out of v1)

- Jazz Fest JS/JSON fallback if static HTML empty in season.
- Extra festivals (Osheaga, etc.).
- Natural-language date parsing (`this sunday`) inside tools — agents pass ISO `date` instead.
