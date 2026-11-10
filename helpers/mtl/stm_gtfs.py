"""Index d'arrêts STM bundlé (extrait de stops.txt GTFS static)."""

from __future__ import annotations

import gzip
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from helpers.mtl.geo import haversine_m

_DATA_PATH = Path(__file__).resolve().parent / "data" / "stm_stops.json.gz"
_MIN_RADIUS_M = 50.0
_MAX_RADIUS_M = 5000.0
_MAX_LIMIT = 50


@lru_cache(maxsize=1)
def load_stops() -> tuple[dict[str, Any], ...]:
    """Charge l'index d'arrêts bundlé (mémoire uniquement)."""
    if not _DATA_PATH.is_file():
        msg = f"Index STM manquant: {_DATA_PATH}. Réinstallez le paquet pour restaurer les données"
        raise FileNotFoundError(msg)
    data = _DATA_PATH.read_bytes()
    if _DATA_PATH.suffix == ".gz":
        data = gzip.decompress(data)
    raw = json.loads(data)
    stops = raw.get("stops") if isinstance(raw, dict) else raw
    if not isinstance(stops, list):
        msg = "stm_stops.json invalide: attendu {stops: [...]} ou liste."
        raise TypeError(msg)
    out: list[dict[str, Any]] = []
    for row in stops:
        if not isinstance(row, dict):
            continue
        stop_id = str(row.get("stop_id") or "").strip()
        if not stop_id:
            continue
        try:
            lat = float(row["lat"])
            lon = float(row["lon"])
        except (KeyError, TypeError, ValueError):
            continue
        item: dict[str, Any] = {
            "stop_id": stop_id,
            "stop_name": row.get("stop_name") or stop_id,
            "latitude": lat,
            "longitude": lon,
        }
        routes = row.get("route_ids")
        if isinstance(routes, list) and routes:
            item["route_ids"] = [str(r) for r in routes if str(r).strip()]
        out.append(item)
    return tuple(out)


def clear_stops_cache() -> None:
    """Invalide le cache (tests)."""
    load_stops.cache_clear()


def filter_stops_nearby(
    stops: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    *,
    latitude: float,
    longitude: float,
    radius_m: float,
    limit: int,
) -> list[dict[str, Any]]:
    """Filtre les arrêts par distance haversine, triés du plus proche."""
    if not (_MIN_RADIUS_M <= radius_m <= _MAX_RADIUS_M):
        msg = f"radius_m doit etre entre {_MIN_RADIUS_M} et {_MAX_RADIUS_M}."
        raise ValueError(msg)
    lim = max(1, min(int(limit), _MAX_LIMIT))
    nearby: list[dict[str, Any]] = []
    for stop in stops:
        dist = haversine_m(latitude, longitude, float(stop["latitude"]), float(stop["longitude"]))
        if dist > radius_m:
            continue
        row = dict(stop)
        row["distance_m"] = round(dist, 1)
        nearby.append(row)
    nearby.sort(key=lambda r: r["distance_m"])
    return nearby[:lim]


def get_stop(stop_id: str) -> dict[str, Any] | None:
    """Lookup d'un arrêt par stop_id."""
    sid = str(stop_id).strip()
    for stop in load_stops():
        if stop["stop_id"] == sid:
            return dict(stop)
    return None
