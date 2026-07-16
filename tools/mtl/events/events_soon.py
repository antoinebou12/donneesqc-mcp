"""Événements bientôt (festivals + civiques)."""

from __future__ import annotations

from helpers.common.response import ok
from helpers.common.tool_call import run_tool
from helpers.common.urls import dq_dataset_url
from helpers.mtl import events_soon
from tools import mcp


@mcp.tool(name="mtl_events_soon")
async def events_soon_tool(
    query: str = "",
    hours: float = 24.0,
    date: str = "",
    timezone: str = "",
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    limit: int = 25,
) -> str:
    """Evenements a venir (Piknic, Jazz Fest, evenements publics) dans les prochaines heures.

    Preferez date/timezone systeme et GPS telephone si disponibles.
    Les festivals n'ont pas de coords - le filtre lieu approx ne s'applique
    qu'aux evenements civiques (arrondissement / adresse).

    Parameters:
        query: Filtre texte optionnel.
        hours: Fenetre a venir (defaut 24, max 168).
        date: YYYY-MM-DD optionnel (sinon maintenant America/Toronto).
        timezone: Fuseau IANA optionnel.
        address: Adresse pour filtre approx civique.
        latitude: Latitude GPS appareil.
        longitude: Longitude GPS appareil.
        limit: Max d'items (1-50).
    """

    async def _run() -> str:
        data = await events_soon.build_events_soon(
            query=query,
            hours=hours,
            date=date,
            timezone_name=timezone,
            address=address,
            latitude=latitude,
            longitude=longitude,
            limit=limit,
        )
        return ok(
            data,
            source="mtl_events_soon",
            portal_url=dq_dataset_url("vmtl-evenements-publics"),
        )

    return await run_tool(
        "events_soon",
        _run,
        generic_error="Impossible de lister les evenements a venir.",
    )
