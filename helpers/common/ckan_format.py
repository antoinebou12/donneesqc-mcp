"""Formatage de payloads CKAN partagés par les tools qc/mtl."""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Any

from helpers.common import ckan_api

if TYPE_CHECKING:
    from helpers.common.portals import Portal

logger = logging.getLogger(__name__)

# UUID entre guillemets dans FROM / JOIN (tables DataStore).
_SQL_RESOURCE_UUID = re.compile(
    r'(?:FROM|JOIN)\s+"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"',
    re.IGNORECASE,
)


def parse_filters_json(filters: str | None) -> dict[str, Any] | None:
    """Parse le JSON filters des tools DataStore.

    Raises:
        ValueError: Si filters n'est pas du JSON objet valide.
    """
    if not filters:
        return None
    try:
        parsed = json.loads(filters)
    except json.JSONDecodeError as exc:
        msg = f"Le paramètre 'filters' n'est pas du JSON valide: {filters}"
        raise ValueError(msg) from exc
    if not isinstance(parsed, dict):
        msg = f"Le paramètre 'filters' doit être un objet JSON: {filters}"
        raise ValueError(msg)  # noqa: TRY004 - surface as validation error to MCP clients
    return parsed


def summarize_package(
    pkg: dict[str, Any],
    portal: Portal,
    *,
    include_tags: bool = False,
    default_organization: str = "",
) -> dict[str, Any]:
    """Résumé compact d'un package CKAN pour les réponses MCP."""
    org = pkg.get("organization") or {}
    summary: dict[str, Any] = {
        "id": pkg.get("id"),
        "name": pkg.get("name"),
        "title": pkg.get("title"),
        "description": (pkg.get("notes") or "")[:300],
        "organization": org.get("title", default_organization) if isinstance(org, dict) else default_organization,
        "num_resources": pkg.get("num_resources", 0),
        "last_modified": pkg.get("metadata_modified"),
        "url": portal.dataset_url(pkg.get("name")),
    }
    if include_tags:
        summary["tags"] = [t["name"] for t in pkg.get("tags", []) if isinstance(t, dict) and "name" in t]
    return summary


def summarize_resources(pkg: dict[str, Any]) -> list[dict[str, Any]]:
    """Liste allégée des ressources d'un package."""
    return [
        {
            "id": r.get("id"),
            "name": r.get("name"),
            "format": r.get("format"),
            "datastore_active": r.get("datastore_active", False),
        }
        for r in pkg.get("resources", [])
    ]


def datastore_payload(
    result: dict[str, Any],
    *,
    page: int | None = None,
    page_size: int | None = None,
    include_sql: str | None = None,
) -> dict[str, Any]:
    """Normalise une réponse datastore_search / datastore_search_sql."""
    fields = [f["id"] for f in result.get("fields", []) if f.get("id") != "_id"]
    payload: dict[str, Any] = {
        "fields": fields,
        "records": result.get("records", []),
    }
    if "total" in result:
        payload["total"] = result.get("total", 0)
    if page is not None:
        payload["page"] = page
    if page_size is not None:
        payload["page_size"] = page_size
    if include_sql is not None:
        payload["sql"] = result.get("sql", include_sql)
    return payload


def select_datastore_resource(
    resources: list[dict[str, Any]],
    *,
    prefer_format: str = "CSV",
) -> dict[str, Any] | None:
    """Choisit une ressource DataStore, en préférant le format demandé."""
    prefer = prefer_format.upper()
    preferred: dict[str, Any] | None = None
    fallback: dict[str, Any] | None = None
    for res in resources:
        if not res.get("datastore_active"):
            continue
        fmt = (res.get("format") or "").upper()
        if fmt == prefer:
            preferred = res
            break
        if fallback is None:
            fallback = res
    return preferred or fallback


def extract_resource_ids_from_sql(sql: str) -> list[str]:
    """Extrait les resource_id (UUID) cités comme tables dans une requête SQL."""
    seen: set[str] = set()
    ordered: list[str] = []
    for match in _SQL_RESOURCE_UUID.finditer(sql):
        rid = match.group(1).lower()
        if rid not in seen:
            seen.add(rid)
            ordered.append(rid)
    return ordered


async def resolve_resource_citation(
    portal: Portal,
    resource_id: str,
) -> dict[str, str]:
    """Construit dataset_url / resource_url pour une ressource (échec soft)."""
    citation: dict[str, str] = {}
    try:
        resource = await ckan_api.resource_show(portal.api_url, resource_id)
        package_id = resource.get("package_id")
        if not package_id:
            return citation
        pkg = await ckan_api.package_show(portal.api_url, str(package_id))
        name = pkg.get("name")
        if not name:
            return citation
        citation["dataset_url"] = portal.dataset_url(str(name))
        citation["resource_url"] = portal.resource_url(str(name), resource_id)
        citation["dataset_name"] = str(name)
        if pkg.get("title"):
            citation["dataset_title"] = str(pkg["title"])
    except Exception:
        # Citation optionnelle : ne doit pas faire échouer la requête DataStore.
        logger.debug("Citation lookup failed for resource %s", resource_id, exc_info=True)
    return citation


def attach_citation_fields(payload: dict[str, Any], citation: dict[str, str]) -> str | None:
    """Copie dataset_url / resource_url / dataset_title dans payload.

    Returns:
        dataset_url si présent (pratique pour portal_url des réponses MCP).
    """
    if citation.get("dataset_url"):
        payload["dataset_url"] = citation["dataset_url"]
    if citation.get("resource_url"):
        payload["resource_url"] = citation["resource_url"]
    if citation.get("dataset_title"):
        payload["dataset_title"] = citation["dataset_title"]
    return citation.get("dataset_url")


def build_package_search_fq(
    *,
    organization: str | None = None,
    tags: str | None = None,
) -> str | None:
    """Construit le filtre Solr ``fq`` pour package_search."""
    parts: list[str] = []
    if organization:
        parts.append(f"organization:{organization}")
    if tags:
        parts.extend(f'tags:"{tag.strip()}"' for tag in tags.split(",") if tag.strip())
    return " AND ".join(parts) if parts else None


def paginate(page: int, page_size: int, *, max_size: int = 100) -> tuple[int, int, int]:
    """Normalise page/page_size et retourne ``(page, size, start/offset)``."""
    safe_page = max(1, page)
    size = max(1, min(page_size, max_size))
    start = (safe_page - 1) * size
    return safe_page, size, start


def parse_search_facet(
    result: dict[str, Any],
    field: str,
    *,
    count_key: str = "datasets",
) -> list[dict[str, str | int]]:
    """Extrait une facette CKAN (``search_facets`` ou fallback ``facets``), triée desc."""
    search_facets = result.get("search_facets") or {}
    facet = search_facets.get(field) or {}
    items = facet.get("items") or []
    if items:
        parsed = [
            {
                "name": item.get("display_name") or item.get("name") or "",
                count_key: int(item.get("count") or 0),
            }
            for item in items
        ]
        return sorted(parsed, key=lambda row: row[count_key], reverse=True)

    raw = (result.get("facets") or {}).get(field) or {}
    return sorted(
        [{"name": name, count_key: int(count)} for name, count in raw.items()],
        key=lambda row: row[count_key],
        reverse=True,
    )


async def search_packages(
    portal: Portal,
    *,
    query: str,
    page: int = 1,
    page_size: int = 20,
    max_page_size: int = 100,
    organization: str | None = None,
    tags: str | None = None,
    include_tags: bool = False,
    default_organization: str = "",
    facet_fields: list[str] | None = None,
) -> dict[str, Any]:
    """Recherche paginée de packages + résumés MCP (portail-agnostique)."""
    safe_page, size, start = paginate(page, page_size, max_size=max_page_size)
    fq = build_package_search_fq(organization=organization, tags=tags)
    result = await ckan_api.package_search(
        portal.api_url,
        query=query,
        rows=size,
        start=start,
        fq=fq,
        facet_fields=facet_fields,
    )
    datasets = [
        summarize_package(
            pkg,
            portal,
            include_tags=include_tags,
            default_organization=default_organization,
        )
        for pkg in result.get("results", [])
    ]
    return {
        "count": result.get("count", 0),
        "page": safe_page,
        "page_size": size,
        "datasets": datasets,
        "_raw": result,
    }
