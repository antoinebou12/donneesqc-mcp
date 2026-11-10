"""Utilitaires géo partagés (haversine, validation WGS84, distance GeoJSON)."""

from __future__ import annotations

import math
from typing import Any

from pyproj import Transformer

_EARTH_RADIUS_M = 6_371_000.0

# NAD83 / MTM zone 8 (Montréal) → WGS84
_MTM8_TO_WGS84 = Transformer.from_crs("EPSG:32188", "EPSG:4326", always_xy=True)


def mtm8_to_wgs84(x: float, y: float) -> tuple[float, float]:
    """Convert NAD83 MTM zone 8 (EPSG:32188) metres to WGS84 (lon, lat)."""
    lon, lat = _MTM8_TO_WGS84.transform(x, y)
    return round(lon, 7), round(lat, 7)


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance orthodromique en mètres entre deux points WGS84."""
    rlat1, rlon1, rlat2, rlon2 = map(math.radians, (lat1, lon1, lat2, lon2))
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return 2 * _EARTH_RADIUS_M * math.asin(math.sqrt(a))


def validate_wgs84(latitude: float, longitude: float) -> None:
    """Raise ValueError if latitude/longitude are outside WGS84 bounds."""
    if not (-90.0 <= latitude <= 90.0):
        msg = "latitude doit etre entre -90 et 90."
        raise ValueError(msg)
    if not (-180.0 <= longitude <= 180.0):
        msg = "longitude doit etre entre -180 et 180."
        raise ValueError(msg)


def iter_lon_lat(geom: dict[str, Any] | None) -> list[tuple[float, float]]:
    """Extract (lon, lat) vertices from Point / LineString / Multi* / Polygon."""
    if not geom:
        return []
    geom_type = geom.get("type")
    coords = geom.get("coordinates")
    if not geom_type or coords is None:
        return []

    points: list[tuple[float, float]] = []

    def _add_pair(pair: Any) -> None:
        if not isinstance(pair, list | tuple) or len(pair) < 2:
            return
        try:
            lon = float(pair[0])
            lat = float(pair[1])
        except (TypeError, ValueError):
            return
        points.append((lon, lat))

    if geom_type == "Point":
        _add_pair(coords)
    elif geom_type in {"MultiPoint", "LineString"}:
        for pair in coords:
            _add_pair(pair)
    elif geom_type == "MultiLineString":
        for line in coords:
            if isinstance(line, list):
                for pair in line:
                    _add_pair(pair)
    elif geom_type == "Polygon":
        if isinstance(coords, list) and coords:
            for pair in coords[0]:
                _add_pair(pair)
    elif geom_type == "MultiPolygon":
        for poly in coords:
            if isinstance(poly, list) and poly:
                for pair in poly[0]:
                    _add_pair(pair)

    return points


def nearest_distance_m(
    latitude: float,
    longitude: float,
    geom: dict[str, Any] | None,
) -> tuple[float, float, float] | None:
    """Return (distance_m, nearest_lat, nearest_lon) or None if no coords."""
    vertices = iter_lon_lat(geom)
    if not vertices:
        return None
    best_dist = float("inf")
    best_lat = 0.0
    best_lon = 0.0
    for lon, lat in vertices:
        dist = haversine_m(latitude, longitude, lat, lon)
        if dist < best_dist:
            best_dist = dist
            best_lat = lat
            best_lon = lon
    return best_dist, best_lat, best_lon
