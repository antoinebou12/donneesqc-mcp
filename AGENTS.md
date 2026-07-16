## Learned User Preferences

- Prefer citing source URLs in responses and in tool JSON (`source` field).
- Prefer sequential-thinking, modern-python, and humanizer when working this repo.
- Prefer production hardening plus docs together (SECURITY.md, ADRs, UML-backed documentation, expanded tests) over security-only or docs-only slices when asked for a full pass.
- Do not re-add `genealogiequebec_search_links` (Généalogie Québec public-links tool); user removed it.
- Prefer NosOrigines unit fixtures with public/historical names (e.g. Samuel de Champlain), not personal names.
- Prefer easy Vercel hosting with a one-click Deploy badge, minimal/no local disk storage, and stronger deployment docs.
- For open-data / MCP Q&A: short verdict + markdown tables + source URLs (no ASCII ranking bars; do not dump JSON `chart`). For dated events attach `calendar_ascii` + `google_calendar_url`; for nearby POIs include Google Maps links. Read `skills/donneesqc-mcp/SKILL.md`.
- Prefer shared helpers and tools that compose on existing ones; keep portal URLs and static source metadata in `helpers/common/urls.py`.
- To smoke EXAMPLES against Docker/MCP: use `.cursor/skills/run-donneesqc-examples/SKILL.md` or `uv run python scripts/smoke_examples.py --live`.

## Learned Workspace Facts

- This repo is a community (not official Québec government) MCP for open data: Données Québec, Données Montréal (CKAN), IGO/iCherche geospatial, Adresses Québec geocoding, plus Montréal civic apps and Hydro-Québec.
- Stack: uv, ruff, ty, pytest; Streamable HTTP only (`POST /mcp`, `GET /health`); tools live under `tools/{qc,mtl,common}/` (domain packages) and register via `register_all_tools()`; MCP names are domain-prefixed (`qc_*`, `mtl_*`, `common_*`).
- Montréal tools nest under `tools/mtl/` (murales, collecte, labicyclette, avis, bixi, parcs, qualo, festivals, evenements, calendar, neighborhood); Hydro-Québec under `tools/qc/hydro`.
- Agent skill for maintain + query workflows: `skills/donneesqc-mcp/SKILL.md` (repo-versioned; not under `.cursor/skills`).
- Extra sources include OQLF Vitrine linguistique and NosOrigines genealogy under `tools/qc/`; both may scrape HTML and must tolerate layout changes; prefer public APIs when available.
- `common_get_context` resolves user date/time (America/Toronto default) and location (agent GPS → address → client IP only; never MCP host egress). Soft defaults feed nearby tools; `mtl_events_soon` covers festivals + civic events in the next N hours.
- NosOrigines uses ASP.NET form posts (VIEWSTATE) and pid-based person pages; treat "Privé" display names as privacy-protected.
- Event/calendar responses use `helpers/common/calendar_format.py`; public events search targets Données Québec package `vmtl-evenements-publics` (cite DQ portal URL).
- SPVM PDQ labels for Montréal crime SQL live in `helpers/mtl/pdq.py` (official names; open data polygons only have `PDQ-N`).
- Infra includes Makefile, Renovate, smithery.yaml, docker-compose, pre-commit, and pip-audit security checks in CI.
- Outbound HTTP caching is in-memory (no heavy local storage), aimed at serverless-friendly hosting.
- Helpers: `helpers/common/` (config, http_client, response, ckan_api, portals, urls, ckan_format, tool_call), `helpers/qc/`, `helpers/mtl/`; tests mirror the same layout under `tests/` with CKAN fixtures in `tests/fixtures/ckan/`.
- Default pytest excludes `@pytest.mark.network`; use `make test-network` for live CKAN checks.
