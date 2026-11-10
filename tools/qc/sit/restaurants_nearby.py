"""Outils SIT Québec — tourisme nearby."""

from __future__ import annotations

from typing import Any

from helpers.common.response import ok
from helpers.common.tool_call import run_tool
from helpers.common.urls import DQ_OPEN_DATA_LICENSE, dq_dataset_url, get_source
from helpers.qc.sit import sit_api
from tools import mcp


def _sit_ok(payload: dict[str, Any], *, dataset_id: str, resource_id: str | None = None) -> str:
    info = get_source("sit_restauration")
    portal = dq_dataset_url(dataset_id)
    body = {k: v for k, v in payload.items() if k not in {"source", "dataset_id", "resource_id"}}
    return ok(
        body,
        source=info["source"],
        portal_url=portal,
        dataset_id=dataset_id,
        resource_id=resource_id,
        license=info.get("license") or DQ_OPEN_DATA_LICENSE,
    )


@mcp.tool(name="qc_sit_restaurants_nearby")
async def qc_sit_restaurants_nearby(
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 500.0,
    limit: int = 15,
) -> str:
    """Restaurants / cafés / cuisine de rue SIT Québec près d'un point (WGS84).

    Source CSV Données Québec (aperçu — pas un recensement exhaustif).
    Note: restaurants, tables champêtres, cafés, crèmes glacées, halles, food trucks.

    Parameters:
        address: Adresse à géocoder (ex. 'Hôtel de Ville de Montréal').
        latitude: Latitude WGS84 (avec longitude).
        longitude: Longitude WGS84.
        radius_m: Rayon en mètres (50-15000, défaut 500).
        limit: Nombre max (1-50, défaut 15).
    """

    async def _run() -> str:
        data = await sit_api.list_nearby(
            address=address,
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            limit=limit,
            category="restauration",
        )
        return _sit_ok(
            data,
            dataset_id=str(data.get("dataset_id") or "sit-quebec-restauration"),
            resource_id=str(data.get("resource_id") or "") or None,
        )

    return await run_tool(
        "qc_sit_restaurants_nearby",
        _run,
        generic_error="Impossible de lister les restaurants SIT a proximite.",
    )


@mcp.tool(name="qc_sit_tourist_nearby")
async def qc_sit_tourist_nearby(
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 500.0,
    limit_per_category: int = 8,
) -> str:
    """POIs touristiques SIT près d'un point: restauration + culture + hôtels + loisirs.

    Aperçu CSV multi-jeux Données Québec (pas exhaustif). Cite chaque source
    sous by_category.

    Parameters:
        address: Adresse à géocoder.
        latitude: Latitude WGS84.
        longitude: Longitude WGS84.
        radius_m: Rayon (50-15000, défaut 500).
        limit_per_category: Max par catégorie SIT (1-50, défaut 8).
    """

    async def _run() -> str:
        data = await sit_api.list_tourist_nearby(
            address=address,
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            limit_per_category=limit_per_category,
        )
        return _sit_ok(data, dataset_id="sit-quebec-restauration")

    return await run_tool(
        "qc_sit_tourist_nearby",
        _run,
        generic_error="Impossible de lister les POIs touristiques SIT.",
    )
