"""Detail MCP d'un compteur cycliste (serie, resume, travaux)."""

from __future__ import annotations

import logging
import re
from datetime import UTC, date, datetime, timedelta
from typing import Any

from helpers.common.config import LABICYCLETTE_BASE_URL
from helpers.common.response import error, ok
from helpers.mtl import labicyclette_api, labicyclette_format
from helpers.mtl.citations import MTL_OPEN_DATA_LICENSE as _LICENSE
from tools import mcp

logger = logging.getLogger(__name__)


_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MAX_SPAN_DAYS = 366


def _parse_iso_date(value: str, label: str) -> date | str:
    """Parse YYYY-MM-DD ou retourne un message d'erreur."""
    if not _DATE_RE.match(value):
        return f"Le parametre {label} doit etre au format YYYY-MM-DD."
    try:
        return date.fromisoformat(value)
    except ValueError:
        return f"Le parametre {label} n'est pas une date valide."


def _default_range() -> tuple[str, str]:
    today = datetime.now(UTC).date()
    start = today - timedelta(days=29)
    return start.isoformat(), today.isoformat()


@mcp.tool(name="mtl_labicyclette_get_counter")
async def get_labicyclette_counter(
    instance: str,
    from_date: str | None = None,
    to_date: str | None = None,
    include_weather: bool = False,
    include_construction: bool = True,
) -> str:
    """Detail MCP d'un compteur (resume + chart ligne, compact par defaut).

    Parameters:
        instance: Identifiant du compteur (ex: '100003032').
        from_date / to_date: Periode YYYY-MM-DD (defaut: 30 derniers jours UTC, max 366 j).
        include_weather: Si true, ajoute tempC/precipMm sur chaque point du chart.
        include_construction: Si true, inclut les chantiers proches (slim).
    """
    try:
        if not instance or not str(instance).strip():
            return error("Le parametre instance est requis.")
        instance = str(instance).strip()

        if from_date is None and to_date is None:
            from_date, to_date = _default_range()
        elif from_date is None or to_date is None:
            return error("Fournir from_date et to_date ensemble, ou aucun des deux.")

        start = _parse_iso_date(from_date, "from_date")
        if isinstance(start, str):
            return error(start)
        end = _parse_iso_date(to_date, "to_date")
        if isinstance(end, str):
            return error(end)

        if start > end:
            return error("from_date doit etre anterieur ou egal a to_date.")
        if (end - start).days > _MAX_SPAN_DAYS:
            return error(f"La plage de dates ne peut pas depasser {_MAX_SPAN_DAYS} jours.")

        raw = await labicyclette_api.get_counter(
            instance,
            from_date=start.isoformat(),
            to_date=end.isoformat(),
        )
        raw_daily = raw.get("dailyData")
        daily: list[dict[str, Any]] = (
            [row for row in raw_daily if isinstance(row, dict)] if isinstance(raw_daily, list) else []
        )
        summary = labicyclette_format.counter_summary(daily)
        points = labicyclette_format.chart_points_from_daily(
            daily,
            include_weather=include_weather,
        )

        construction: list | None = None
        if include_construction:
            active = raw.get("activeConstruction")
            if isinstance(active, list):
                construction = [
                    labicyclette_format.slim_construction_near_counter(row) for row in active if isinstance(row, dict)
                ]
            else:
                construction = []

        site = labicyclette_format.slim_counter_site(raw)
        if not site["instance"]:
            site["instance"] = instance

        payload = {
            "view": "counter",
            "counter": site,
            "period": {"from": start.isoformat(), "to": end.isoformat()},
            "summary": summary,
            "chart": labicyclette_format.line_chart(points),
            "construction": construction,
            "weather": (
                {
                    "included": True,
                    "meta": raw.get("weatherMeta"),
                }
                if include_weather
                else None
            ),
        }
        return ok(
            payload,
            source="labicyclette",
            portal_url=LABICYCLETTE_BASE_URL,
            license=_LICENSE,
        )
    except Exception:
        logger.exception("Erreur dans get_labicyclette_counter")
        return error(f"Impossible de recuperer le compteur '{instance}'.")
