# ADR 0001: Community Project, Not Official Government Service

## Status

Accepted

## Context

Données Québec MCP helps AI agents search, inspect and analyze open data from public Québec data portals such as Données Québec, Données Montréal, IGO/iCherche, OQLF Vitrine linguistique and NosOrigines public pages. The project is maintained by the community and is not operated, endorsed or certified by the Gouvernement du Québec.

Users may naturally assume that a Québec open-data assistant is official or can perform citizen services. That would be misleading and unsafe.

## Decision

The project will present itself as a community MCP server for open data only. Documentation, response metadata and security notes must state that this is not an official government service.

The supported scope is:

- discovery and analysis of public open-data catalogues;
- read-only CKAN DataStore queries;
- public geospatial lookup and geocoding;
- public linguistic and genealogy lookup where allowed by the upstream site.

The unsupported scope is:

- tax filing, health records, identity records or authenticated citizen portals;
- automated actions on behalf of a citizen or organization;
- scraping Québec.ca as a general government website crawler;
- overriding dataset licences or upstream terms of use.

## Consequences

- Tool responses include additive `_meta` provenance and disclaimer fields.
- README and SECURITY documentation must make the community/non-official status explicit.
- New tools should prefer official public APIs and open-data endpoints over fragile scraping.
- Licence checks remain the responsibility of users and downstream agents.
