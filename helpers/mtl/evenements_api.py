"""Événements publics Montréal via CKAN (vmtl-evenements-publics).

Primary portal: Données Québec; fallback: Données Montréal.
"""

from __future__ import annotations

import logging
from datetime import date as date_type
from typing import Any

from helpers.common import ckan_api
from helpers.common.config import EVENEMENTS_CSV_RESOURCE_ID, EVENEMENTS_PACKAGE_ID
from helpers.common.maps_format import google_maps_url
from helpers.common.portals import DQ_PORTAL, MTL_PORTAL, Portal
from helpers.mtl.avis_api import active_on
from helpers.mtl.calendar_adapters import enrich_list_payload, evenement_row_to_item
from helpers.mtl.events_common import clamp_limit, validate_optional_iso_date

logger = logging.getLogger(__name__)

PACKAGE_ID = EVENEMENTS_PACKAGE_ID
KNOWN_CSV_RESOURCE_IDS = (EVENEMENTS_CSV_RESOURCE_ID,)


def _pick_datastore_resource(pkg: dict[str, Any]) -> dict[str, Any] | None:
    resources = pkg.get("resources") or []
    active = [r for r in resources if r.get("datastore_active")]
    if not active:
        for rid in KNOWN_CSV_RESOURCE_IDS:
            for r in resources:
                if r.get("id") == rid:
                    return r
        return None
    for r in active:
        fmt = (r.get("format") or "").upper()
        if fmt == "CSV":
            return r
    return active[0]


async def _resolve_on_portal(portal: Portal) -> tuple[dict[str, Any], dict[str, Any]]:
    pkg = await ckan_api.package_show(portal.api_url, PACKAGE_ID)
    resource = _pick_datastore_resource(pkg)
    if resource is None:
        msg = f"Aucune ressource DataStore pour {PACKAGE_ID} sur {portal.source}."
        raise RuntimeError(msg)
    return pkg, resource


async def resolve_package_and_resource() -> tuple[Portal, dict[str, Any], dict[str, Any], str | None]:
    """DQ first, then MTL. Returns portal, package, resource, optional note."""
    note: str | None = None
    try:
        pkg, resource = await _resolve_on_portal(DQ_PORTAL)
    except Exception as exc:
        logger.info("evenements: DQ failed (%s); trying MTL", exc)
        note = f"Données Québec indisponible ({exc}); bascule vers Données Montréal."
        pkg, resource = await _resolve_on_portal(MTL_PORTAL)
        return MTL_PORTAL, pkg, resource, note
    else:
        return DQ_PORTAL, pkg, resource, note


def _normalize_row(raw: dict[str, Any]) -> dict[str, Any]:
    row = {
        "titre": raw.get("titre") or raw.get("title") or "",
        "type_evenement": raw.get("type_evenement") or raw.get("type") or "",
        "date_debut": raw.get("date_debut"),
        "date_fin": raw.get("date_fin"),
        "emplacement": raw.get("emplacement") or "",
        "arrondissement": raw.get("arrondissement") or "",
        "adresse_principale": raw.get("adresse_principale") or "",
        "url_fiche": raw.get("url_fiche") or raw.get("url") or "",
        "cout": raw.get("cout"),
        "public_cible": raw.get("public_cible"),
    }
    address = str(row["adresse_principale"] or row["emplacement"] or "").strip()
    maps = google_maps_url(address=address or None)
    if maps is not None:
        row["google_maps_url"] = maps
    return row


def _row_matches_query(row: dict[str, Any], query: str) -> bool:
    q = query.strip().lower()
    if not q:
        return True
    hay = " ".join(
        [
            str(row.get("titre") or ""),
            str(row.get("type_evenement") or ""),
            str(row.get("emplacement") or ""),
            str(row.get("arrondissement") or ""),
            str(row.get("adresse_principale") or ""),
        ]
    ).lower()
    return q in hay


def _row_active_on(row: dict[str, Any], target: date_type) -> bool:
    return active_on(target, row.get("date_debut"), row.get("date_fin"))


def filter_evenements(
    rows: list[dict[str, Any]],
    *,
    query: str = "",
    on_date: str = "",
) -> list[dict[str, Any]]:
    """Filter normalized events by substring query and optional active date."""
    filtered = rows
    if query and query.strip():
        filtered = [r for r in filtered if _row_matches_query(r, query)]
    if on_date:
        target = date_type.fromisoformat(on_date)
        filtered = [r for r in filtered if _row_active_on(r, target)]
    return filtered


async def search_evenements(
    *,
    query: str = "",
    date: str = "",
    limit: int = 25,
) -> dict[str, Any]:
    """Search civic public events; attach calendar fields."""
    on_date = validate_optional_iso_date(date)
    limit = clamp_limit(limit)

    portal, pkg, resource, note = await resolve_package_and_resource()
    resource_id = str(resource["id"])
    result = await ckan_api.datastore_search(
        portal.api_url,
        resource_id,
        q=query.strip() or None,
        limit=min(max(limit * 4, 100), 500),
        offset=0,
    )
    records = result.get("records") or []
    normalized = [_normalize_row(r) for r in records if isinstance(r, dict)]
    filtered = filter_evenements(normalized, query=query, on_date=on_date)
    capped = filtered[:limit]

    dq_dataset_url = DQ_PORTAL.dataset_url(PACKAGE_ID)
    portal_dataset_url = portal.dataset_url(PACKAGE_ID)

    warning = note
    if not capped and not normalized:
        warning = (warning + " " if warning else "") + (
            "Aucun evenement retourne par le DataStore (hors saison ou schema change)."
        )
    elif not capped:
        warning = (warning + " " if warning else "") + "Aucun evenement ne correspond aux filtres."

    payload: dict[str, Any] = {
        "query": query or "",
        "date": on_date or "",
        "count": len(capped),
        "events": capped,
        "warning": warning,
        "dataset": PACKAGE_ID,
        "resource_id": resource_id,
        "portal_used": portal.source,
        "alternate_portal_note": (
            "Jeu de donnees civique Montreal publie sur Donnees Quebec "
            f"({dq_dataset_url}); miroir possible sur Donnees Montreal."
        ),
    }
    payload = enrich_list_payload(payload, list_key="events", mapper=evenement_row_to_item)
    payload["_portal"] = {
        "source": portal.source,
        "portal_url": dq_dataset_url if portal is DQ_PORTAL else portal_dataset_url,
        "dq_dataset_url": dq_dataset_url,
        "mtl_dataset_url": MTL_PORTAL.dataset_url(PACKAGE_ID),
        "license": pkg.get("license_title") or pkg.get("license_id"),
    }
    return payload
