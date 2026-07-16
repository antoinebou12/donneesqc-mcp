# ADR 0002: SQL Validation and HTTP Hardening

## Status

Accepted

## Context

The MCP exposes read-only tools over public CKAN DataStore endpoints and upstream HTTP services. Agents can generate high-volume or malformed requests, and SQL strings can contain accidental or hostile write statements if not constrained.

The project should be safe by default without adding infrastructure that makes local, Docker, Smithery or serverless hosting harder.

## Decision

Use application-level guards:

- Validate DataStore SQL with `sqlglot` using a Postgres-like dialect before calling `datastore_search_sql`.
- Allow only one read-only statement: `SELECT`, set operations, or `WITH ... SELECT`.
- Reject `SELECT INTO`, multi-statement SQL, oversized SQL through `SQL_MAX_LENGTH`, and write-oriented keywords as defense in depth.
- Rate limit outbound HTTP with an in-memory token bucket per host using `HTTP_RATE_LIMIT_RPS` and `HTTP_RATE_LIMIT_BURST`.
- Cache successful GET responses in a bounded in-memory TTL/LRU cache using `HTTP_CACHE_TTL_SECONDS` and `HTTP_CACHE_MAX_ENTRIES`.
- Keep SQL DataStore calls uncached because they may be dynamic and large.
- Enforce `DOWNLOAD_MAX_BYTES` before and during streamed downloads.
- Do not add Redis or another external cache dependency.

## Consequences

- The default deployment remains simple: one Python process and no required local disk or network cache.
- Rate limits and cache state are per process, so horizontally scaled deployments do not share buckets or cache entries.
- In-memory cache entries disappear on process restart, which is acceptable for this project's availability and hosting goals.
- The SQL validator reduces risk but is not a formal database sandbox; upstream CKAN permissions and read-only API behavior remain part of the security boundary.
