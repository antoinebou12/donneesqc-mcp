"""Formatters MCP-first pour les reponses La bicyclette."""

from __future__ import annotations

from typing import Any

from helpers.common.chart_format import bar_chart

__all__ = [
    "bar_chart",
    "build_overview_kpis",
    "chart_points_from_daily",
    "counter_name",
    "counter_summary",
    "format_boroughs",
    "format_compact_number",
    "line_chart",
    "map_points",
    "slim_construction",
    "slim_construction_near_counter",
    "slim_counter_site",
]


def format_compact_number(value: int | float | None) -> str:
    """Formate un nombre pour affichage UI (180.3M, 42.2K, 81)."""
    if value is None:
        return "N/A"
    n = float(value)
    sign = "-" if n < 0 else ""
    n = abs(n)
    if n >= 1_000_000_000:
        return f"{sign}{n / 1_000_000_000:.1f}".rstrip("0").rstrip(".") + "B"
    if n >= 1_000_000:
        return f"{sign}{n / 1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
    if n >= 1_000:
        return f"{sign}{n / 1_000:.1f}".rstrip("0").rstrip(".") + "K"
    if n == int(n):
        return f"{sign}{int(n)}"
    return f"{sign}{n:.1f}".rstrip("0").rstrip(".")


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def build_overview_kpis(
    total_volume: int,
    active_counters: int,
    daily_average: int,
) -> list[dict[str, Any]]:
    """Cartes KPI style tableau de bord Overview."""
    return [
        {
            "id": "total_rides",
            "label": "Total Rides",
            "value": total_volume,
            "display": format_compact_number(total_volume),
        },
        {
            "id": "active_counters",
            "label": "Active Counters",
            "value": active_counters,
            "display": format_compact_number(active_counters),
        },
        {
            "id": "daily_average",
            "label": "Daily Average",
            "value": daily_average,
            "display": format_compact_number(daily_average),
        },
    ]


def line_chart(
    points: list[dict[str, Any]],
    *,
    metric: str = "volume",
) -> dict[str, Any]:
    """Serie temporelle pour graphiques ligne."""
    return {"type": "line", "metric": metric, "points": points}


def map_points(points: list[dict[str, Any]]) -> dict[str, Any]:
    """Points carte (compteurs ou chantiers)."""
    return {"type": "map_points", "points": points}


def counter_name(row: dict[str, Any]) -> str:
    """Nom affiche d'un compteur."""
    rue1 = row.get("rue1")
    if rue1:
        return str(rue1)
    instance = row.get("instance")
    return str(instance) if instance is not None else "Unknown"


def slim_counter_site(row: dict[str, Any]) -> dict[str, Any]:
    """Site compteur pour listes MCP."""
    return {
        "instance": str(row.get("instance") or ""),
        "name": counter_name(row),
        "borough": row.get("arrondissement"),
        "latitude": _as_float(row.get("latitude")),
        "longitude": _as_float(row.get("longitude")),
    }


def counter_summary(daily_data: list[dict[str, Any]]) -> dict[str, Any]:
    """Agregats volume a partir de dailyData."""
    volumes: list[tuple[str, int]] = []
    for day in daily_data:
        if not isinstance(day, dict):
            continue
        date = day.get("date")
        volume = _as_int(day.get("volume"), default=-1)
        if date is None or volume < 0:
            continue
        volumes.append((str(date), volume))

    if not volumes:
        return {
            "totalVolume": 0,
            "dailyAverage": 0,
            "daysWithData": 0,
            "peak": None,
            "low": None,
        }

    total = sum(v for _, v in volumes)
    peak_date, peak_vol = max(volumes, key=lambda x: x[1])
    low_date, low_vol = min(volumes, key=lambda x: x[1])
    days = len(volumes)
    return {
        "totalVolume": total,
        "dailyAverage": round(total / days) if days else 0,
        "daysWithData": days,
        "peak": {"date": peak_date, "volume": peak_vol},
        "low": {"date": low_date, "volume": low_vol},
    }


def chart_points_from_daily(
    daily_data: list[dict[str, Any]],
    *,
    include_weather: bool = False,
) -> list[dict[str, Any]]:
    """Points chart (volume + meteo optionnelle)."""
    points: list[dict[str, Any]] = []
    for day in daily_data:
        if not isinstance(day, dict):
            continue
        date = day.get("date")
        if date is None:
            continue
        point: dict[str, Any] = {
            "date": str(date),
            "volume": _as_int(day.get("volume")),
        }
        if include_weather:
            temp = _as_float(day.get("temperatureMeanC"))
            precip = _as_float(day.get("precipitationMm"))
            if temp is not None:
                point["tempC"] = temp
            if precip is not None:
                point["precipMm"] = precip
        points.append(point)
    return points


def slim_construction_near_counter(row: dict[str, Any]) -> dict[str, Any]:
    """Chantier lie a un compteur (detail)."""
    raw_impact = row.get("impact")
    impact: dict[str, Any] = raw_impact if isinstance(raw_impact, dict) else {}
    return {
        "permitId": row.get("permitId"),
        "status": row.get("status"),
        "distanceMeters": row.get("distanceMeters")
        if row.get("distanceMeters") is not None
        else row.get("nearestCounterDistanceMeters"),
        "signal": impact.get("signal") or row.get("signal"),
        "duringDeltaPct": impact.get("duringDeltaPct")
        if impact.get("duringDeltaPct") is not None
        else row.get("duringDeltaPct"),
    }


def slim_construction(row: dict[str, Any]) -> dict[str, Any]:
    """Ligne chantier pour listes MCP."""
    raw_impact = row.get("impact")
    impact: dict[str, Any] = raw_impact if isinstance(raw_impact, dict) else {}
    street = row.get("streetName") or row.get("street") or row.get("streetShortName")
    return {
        "permitId": row.get("permitId"),
        "streetName": street,
        "borough": row.get("borough"),
        "status": row.get("status"),
        "severityScore": _as_int(row.get("severityScore")),
        "startDate": row.get("startDate"),
        "endDate": row.get("endDate"),
        "latitude": _as_float(row.get("latitude")),
        "longitude": _as_float(row.get("longitude")),
        "nearestCounterInstance": row.get("nearestCounterInstance"),
        "nearestCounterName": row.get("nearestCounterName"),
        "impact": {
            "signal": impact.get("signal"),
            "duringDeltaPct": impact.get("duringDeltaPct"),
        },
        "snapshotDate": row.get("snapshotDate"),
    }


def format_boroughs(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Boroughs classes avec parts et chart bar."""
    cleaned: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        borough = row.get("borough")
        if not borough:
            continue
        cleaned.append(
            {
                "borough": str(borough),
                "volume": _as_int(row.get("volume")),
                "counterCount": _as_int(row.get("counterCount")),
            }
        )
    cleaned.sort(key=lambda r: r["volume"], reverse=True)
    total = sum(r["volume"] for r in cleaned) or 1
    boroughs: list[dict[str, Any]] = []
    for i, row in enumerate(cleaned, start=1):
        share = round(100.0 * row["volume"] / total, 1)
        boroughs.append(
            {
                "rank": i,
                "borough": row["borough"],
                "volume": row["volume"],
                "display": format_compact_number(row["volume"]),
                "counterCount": row["counterCount"],
                "volumeSharePct": share,
            }
        )
    return {
        "count": len(boroughs),
        "boroughs": boroughs,
        "chart": bar_chart(
            [b["borough"] for b in boroughs],
            [b["volume"] for b in boroughs],
        ),
    }
