# Changelog

## [Unreleased]

### Added

- `mtl_neighborhood_briefing` — briefing de quartier (Hydro + avis + QUALO + parcs + BIXI, succès partiel)
- `mtl_parcs_nearby` / `mtl_bixi_nearby` / `mtl_qualo_nearby` — proximité unitaire
- `qc_hydro_outage_status` — état du service Info-pannes (adresse ou lat/lng via Adresses Québec)
- `mtl_avis_nearby` — avis/alertes Montréal actifs à une date, près d'une adresse (GeoJSON)
- `qc_get_catalog_stats` — thèmes CKAN (`top_groups`) + filtre optionnel `organization`
- sqlglot-based SQL validation, HTTP rate limiting and GET cache
- `_meta` citation envelope on tool responses
- SECURITY.md, ADRs, architecture docs, GitHub templates, release workflow, devcontainer

### Changed

- Scénarios nearby / smoke / sample : adresse publique **Hôtel de Ville de Montréal** (`275 Rue Notre-Dame Est`)
- Hardened outbound HTTP client
- IGO WFS `qc_geo_get_features` : `outputFormat=geojson` + `typeNames` (IGO MapServer)
- EXAMPLES.md : §45 briefing de quartier + couverture nearby (parcs / BIXI / QUALO)
- Refactor DRY : `ckan_format` (`search_packages`, `paginate`, `build_package_search_fq`, `parse_search_facet`, `attach_citation_fields`), `events_common` (filtres festivals), `validate_wgs84` ; tools qc/mtl search/query/festivals/catalog_stats s'appuient dessus
- Skill `donneesqc-mcp` : flux et règles de présentation pour briefing de quartier
- CI / `make security` : `bandit` (SAST) + `detect-secrets` (clés API / secrets) en plus de `pip-audit`
