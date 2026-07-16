"""Google Maps place-pin and directions URLs for POI / nearby tool payloads.

Chat agents should present nearby results as a Dist. | label | Maps table and
surface ``nearest_google_maps_directions_url`` once (see skills/donneesqc-mcp).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote


def google_maps_url(
    *,
    latitude: float | None = None,
    longitude: float | None = None,
    address: str | None = None,
) -> str | None:
    """Build a Google Maps search (place pin) URL, or None if no usable query."""
    if latitude is not None and longitude is not None:
        query = f"{float(latitude)},{float(longitude)}"
        return f"https://www.google.com/maps/search/?api=1&query={quote(query, safe=',')}"

    cleaned = (address or "").strip()
    if cleaned:
        return f"https://www.google.com/maps/search/?api=1&query={quote(cleaned)}"
    return None


def google_maps_directions_url(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
) -> str:
    """Build a Google Maps directions URL between two WGS84 points."""
    origin = quote(f"{float(origin_lat)},{float(origin_lon)}", safe=",")
    dest = quote(f"{float(dest_lat)},{float(dest_lon)}", safe=",")
    return f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={dest}"


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def attach_maps_pin(
    row: dict[str, Any],
    *,
    lat_key: str = "latitude",
    lon_key: str = "longitude",
    address_key: str | None = None,
) -> dict[str, Any]:
    """Set ``google_maps_url`` on a copy of ``row`` when coords or address exist."""
    out = dict(row)
    lat = _as_float(out.get(lat_key))
    lon = _as_float(out.get(lon_key))
    address: str | None = None
    if address_key:
        raw = out.get(address_key)
        address = str(raw).strip() if raw is not None and str(raw).strip() else None
    url = google_maps_url(latitude=lat, longitude=lon, address=address)
    if url is not None:
        out["google_maps_url"] = url
    return out


def attach_nearby_maps(
    items: list[dict[str, Any]],
    *,
    query_lat: float,
    query_lon: float,
    lat_key: str = "latitude",
    lon_key: str = "longitude",
    address_key: str | None = None,
) -> tuple[list[dict[str, Any]], str | None]:
    """Pin every item; add directions only on the first (nearest) with coords.

    Returns ``(enriched_items, nearest_google_maps_directions_url)``.
    """
    enriched: list[dict[str, Any]] = []
    nearest_directions: str | None = None

    for index, item in enumerate(items):
        row = attach_maps_pin(
            item,
            lat_key=lat_key,
            lon_key=lon_key,
            address_key=address_key,
        )
        if index == 0 and nearest_directions is None:
            dest_lat = _as_float(row.get(lat_key))
            dest_lon = _as_float(row.get(lon_key))
            if dest_lat is not None and dest_lon is not None:
                directions = google_maps_directions_url(
                    query_lat,
                    query_lon,
                    dest_lat,
                    dest_lon,
                )
                row["google_maps_directions_url"] = directions
                nearest_directions = directions
        enriched.append(row)

    return enriched, nearest_directions
