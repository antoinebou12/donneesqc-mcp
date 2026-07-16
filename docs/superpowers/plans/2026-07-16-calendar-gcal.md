# Calendar ASCII + Google Calendar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add day-agenda `calendar_ascii` and per-item `google_calendar_url` to festival/avis/evenements tools, plus `mtl_evenements_search` and `mtl_calendar_week`.

**Architecture:** Shared `CalendarItem` + `helpers/common/calendar_format.py`; MTL adapters; enrich existing tools; new CKAN evenements helper (DQ primary, MTL fallback); week aggregator merges sources.

**Tech Stack:** Python 3, uv, pytest, existing `ckan_api` / `ok` / `run_tool`, Google Calendar TEMPLATE URLs.

**Spec:** [docs/superpowers/specs/2026-07-16-calendar-gcal-design.md](../specs/2026-07-16-calendar-gcal-design.md)

## Global Constraints

- Day-agenda ASCII only (layout C); no ASCII bar charts in chat skill rules.
- Every dated event/alert gets `google_calendar_url`; undated → `null`, excluded from ASCII.
- No disk persistence; no invented showtimes.
- Primary evenements portal: Données Québec CKAN; cite DQ in `_meta`; MTL fallback allowed.
- French user-facing errors; `make check` before done.

---

## Task 1: `calendar_format` helper (TDD)

**Files:**
- Create: `helpers/common/calendar_format.py`
- Create: `tests/common/test_calendar_format.py`

- [ ] Write failing tests for `google_calendar_url` (timed + all-day), `calendar_ascii` day grouping, undated omitted.
- [ ] Implement `CalendarItem`, `google_calendar_url`, `calendar_ascii`, `attach_calendar`.
- [ ] Run `uv run pytest tests/common/test_calendar_format.py` — pass.

## Task 2: Adapters

**Files:**
- Create: `helpers/mtl/calendar_adapters.py`
- Create: `tests/mtl/test_calendar_adapters.py`

- [ ] Tests mapping festival event, avis alert, evenement row → `CalendarItem`.
- [ ] Implement adapters; reuse existing fixtures where possible.
- [ ] Pytest pass.

## Task 3: `mtl_evenements_search`

**Files:**
- Create: `helpers/mtl/evenements_api.py`
- Create: `tools/mtl/evenements/__init__.py`, `tools/mtl/evenements/search_evenements.py`
- Create: `tests/mtl/evenements/test_evenements.py` + fixture JSON under `tests/fixtures/`
- Modify: `tools/__init__.py` (register import)

- [ ] Failing tests (mock CKAN): query/date filter, DQ then MTL fallback, calendar fields, `_meta`.
- [ ] Implement API + tool with `attach_calendar`.
- [ ] Pytest pass.

## Task 4: Enrich festivals + avis

**Files:**
- Modify: `tools/mtl/festivals/*.py`, `helpers/mtl/piknic_api.py` and/or `jazzfest_api.py` (attach at helper or tool layer — prefer one place).
- Modify: `tools/mtl/avis/find_avis_nearby.py` and/or `helpers/mtl/avis_api.py`
- Modify: existing festival/avis tests

- [ ] Assert `google_calendar_url` on dated rows and `calendar_ascii` on success payloads.
- [ ] Pytest pass for festivals + avis.

## Task 5: `mtl_calendar_week` aggregator

**Files:**
- Create: `tools/mtl/calendar/__init__.py`, `tools/mtl/calendar/week.py`
- Create: `helpers/mtl/calendar_week.py` (orchestration)
- Create: `tests/mtl/calendar/test_calendar_week.py`
- Modify: `tools/__init__.py`

- [ ] Tests: merge mock sources; avis skipped without geo + warning; ASCII + GCal.
- [ ] Implement; register tool.
- [ ] Pytest pass.

## Task 6: Skill + docs

**Files:**
- Modify: `skills/donneesqc-mcp/SKILL.md`, `reference.md`
- Modify: `EXAMPLES.md`, `README.md`, `tools/common/list_tools_with_examples.py`
- Modify: `tools/__init__.py` MCP instructions
- Add `.superpowers/` to `.gitignore` if missing

- [ ] Document day-agenda ASCII + GCal; new tools; keep no ASCII bars.
- [ ] `make check`

## Done when

- Dated items from festivals, avis, evenements expose `google_calendar_url`.
- Those responses include layout-C `calendar_ascii`.
- `mtl_evenements_search` and `mtl_calendar_week` registered and tested.
- Skill/EXAMPLES/README updated; `make check` green.
