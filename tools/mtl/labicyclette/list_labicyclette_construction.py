"""Chantiers actifs impactant les pistes - contrat MCP construction."""

from __future__ import annotations

import logging

from helpers.common.config import LABICYCLETTE_BASE_URL
from helpers.common.response import error, ok
from helpers.mtl import labicyclette_api, labicyclette_format
from helpers.mtl.citations import MTL_OPEN_DATA_LICENSE as _LICENSE
from tools import mcp

logger = logging.getLogger(__name__)


_ALLOWED_STATUS = frozenset({"blocked", "obstructed"})


@mcp.tool(name="mtl_labicyclette_list_construction")
async def list_labicyclette_construction(
    status: str | None = None,
    borough: str | None = None,
    min_severity: int = 0,
    limit: int = 25,
) -> str:
    """Liste MCP des chantiers actifs impactant les pistes cyclables.

    Filtrage cote MCP (l'API amont renvoie tout le snapshot).
    Retourne sites slim + chart map_points.

    Parameters:
        status: 'blocked', 'obstructed', ou omit pour tous.
        borough: Filtre partiel insensible a la casse.
        min_severity: Score minimum 0-100 (defaut 0).
        limit: Nombre max de sites retournes (1-50, defaut 25).
    """
    try:
        limit = max(1, min(int(limit), 50))
        min_severity = max(0, min(int(min_severity), 100))

        if status is not None and status.strip():
            status_norm = status.strip().casefold()
            if status_norm not in _ALLOWED_STATUS:
                return error("status doit etre 'blocked', 'obstructed', ou omis.")
        else:
            status_norm = None

        rows = await labicyclette_api.list_construction()
        matched: list[dict] = []
        for row in rows:
            row_status = str(row.get("status") or "").casefold()
            if status_norm and row_status != status_norm:
                continue
            if borough and borough.strip():
                needle = borough.strip().casefold()
                if needle not in str(row.get("borough") or "").casefold():
                    continue
            severity = int(row.get("severityScore") or 0)
            if severity < min_severity:
                continue
            matched.append(row)

        # Prioriser severite desc puis status blocked
        matched.sort(
            key=lambda r: (
                int(r.get("severityScore") or 0),
                1 if str(r.get("status") or "").casefold() == "blocked" else 0,
            ),
            reverse=True,
        )

        slim = [labicyclette_format.slim_construction(r) for r in matched[:limit]]
        snapshot = next(
            (s.get("snapshotDate") for s in slim if s.get("snapshotDate")),
            None,
        )
        points = [
            {
                "lat": s["latitude"],
                "lon": s["longitude"],
                "status": s.get("status"),
                "severityScore": s.get("severityScore"),
                "label": s.get("streetName") or s.get("permitId"),
            }
            for s in slim
            if s.get("latitude") is not None and s.get("longitude") is not None
        ]

        return ok(
            {
                "view": "construction",
                "count": len(slim),
                "total_matching": len(matched),
                "snapshot_date": snapshot,
                "sites": slim,
                "chart": labicyclette_format.map_points(points),
            },
            source="labicyclette",
            portal_url=LABICYCLETTE_BASE_URL,
            license=_LICENSE,
        )
    except Exception:
        logger.exception("Erreur dans list_labicyclette_construction")
        return error("Impossible de lister les chantiers La bicyclette.")
