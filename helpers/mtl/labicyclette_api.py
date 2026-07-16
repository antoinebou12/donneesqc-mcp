"""Client HTTP pour l'API JSON non officielle de La bicyclette."""

from __future__ import annotations

import json
from typing import Any

from helpers.common.config import LABICYCLETTE_BASE_URL
from helpers.common.http_client import fetch_json, fetch_text


def _parse_json_list(text: str, endpoint: str) -> list[dict[str, Any]]:
    data = json.loads(text)
    if not isinstance(data, list):
        msg = f"Reponse inattendue de {endpoint} (tableau JSON attendu)."
        raise TypeError(msg)
    return [row for row in data if isinstance(row, dict)]


async def get_overview() -> dict[str, Any]:
    """GET /api/stats/overview - KPIs agreges (non filtrables par date)."""
    data = await fetch_json(f"{LABICYCLETTE_BASE_URL}/api/stats/overview")
    if not isinstance(data, dict):
        msg = "Reponse inattendue de /api/stats/overview (objet JSON attendu)."
        raise TypeError(msg)
    return data


async def list_counters() -> list[dict[str, Any]]:
    """GET /api/counters - liste des sites de comptage."""
    text = await fetch_text(f"{LABICYCLETTE_BASE_URL}/api/counters")
    return _parse_json_list(text, "/api/counters")


async def get_counter(instance: str, from_date: str, to_date: str) -> dict[str, Any]:
    """GET /api/counters/{instance}?from=&to= - volumes quotidiens + meteo + travaux."""
    data = await fetch_json(
        f"{LABICYCLETTE_BASE_URL}/api/counters/{instance}",
        params={"from": from_date, "to": to_date},
    )
    if not isinstance(data, dict):
        msg = f"Reponse inattendue de /api/counters/{instance} (objet JSON attendu)."
        raise TypeError(msg)
    return data


async def get_boroughs() -> list[dict[str, Any]]:
    """GET /api/stats/boroughs - volumes par arrondissement (totaux all-time)."""
    text = await fetch_text(f"{LABICYCLETTE_BASE_URL}/api/stats/boroughs")
    return _parse_json_list(text, "/api/stats/boroughs")


async def list_construction() -> list[dict[str, Any]]:
    """GET /api/construction/active - chantiers impactant les pistes."""
    text = await fetch_text(f"{LABICYCLETTE_BASE_URL}/api/construction/active")
    return _parse_json_list(text, "/api/construction/active")
