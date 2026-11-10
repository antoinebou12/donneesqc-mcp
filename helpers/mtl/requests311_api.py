"""Bounded nearby search of published citizen requests."""

import math
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from helpers.common import ckan_api
from helpers.common.config import DQ_API_URL
from helpers.common.maps_format import attach_nearby_maps
from helpers.common.urls import DQ_311_SOURCE_URL, MTL_311_RESOURCE_ID, MTL_311_SOURCE_URL
from helpers.mtl.geo import haversine_m
from helpers.mtl.nearby import resolve_point

MAX_CANDIDATES = 2000


async def list_nearby(
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 800,
    days: int = 30,
    limit: int = 10,
    use_latest_available: bool = False,
) -> dict:
    """Return recent geolocated requests; never infer intervention from status."""
    if not math.isfinite(radius_m) or not 100 <= radius_m <= 3000:
        raise ValueError("Le rayon doit être compris entre 100 et 3000 mètres.")
    if not 1 <= days <= 90 or not 1 <= limit <= 50:
        raise ValueError("days doit être entre 1 et 90; limit entre 1 et 50.")
    lat, lon, resolved = await resolve_point(address=address, latitude=latitude, longitude=longitude)
    today = datetime.now(ZoneInfo("America/Toronto")).date()
    latest_date = None
    if use_latest_available:
        latest = await ckan_api.datastore_search_sql(
            DQ_API_URL,
            f'SELECT "DDS_DATE_CREATION" FROM "{MTL_311_RESOURCE_ID}" '  # noqa: S608
            'WHERE "LOC_LAT" IS NOT NULL AND "LOC_LONG" IS NOT NULL '
            'ORDER BY "DDS_DATE_CREATION" DESC LIMIT 1',
        )
        available = latest.get("records") or []
        if available:
            latest_date = date.fromisoformat(str(available[0]["DDS_DATE_CREATION"])[:10])
    anchor = min(today, latest_date) if latest_date else today
    since = (anchor - timedelta(days=days - 1)).isoformat()
    until = (anchor + timedelta(days=1)).isoformat()
    dy = radius_m / 111_320
    dx = dy / max(0.2, abs(math.cos(math.radians(lat))))
    if not (45.3 <= lat <= 45.8 and -74.1 <= lon <= -73.4):
        raise ValueError("Choisissez un lieu dans la région de Montréal.")
    # Montréal coordinates have fixed-width integer parts. Bound text columns
    # lexically, then validate and filter exact distances below without SQL casts.
    lat_low, lat_high = sorted((str(lat - dy), str(lat + dy)))
    lon_low, lon_high = sorted((str(lon - dx), str(lon + dx)))
    sql = (
        'SELECT "ACTI_NOM", "NATURE", "DDS_DATE_CREATION", "DERNIER_STATUT", '  # noqa: S608
        '"DATE_DERNIER_STATUT", "ARRONDISSEMENT_GEO", "LOC_LAT", "LOC_LONG" '
        f'FROM "{MTL_311_RESOURCE_ID}" '
        f"WHERE \"DDS_DATE_CREATION\" >= '{since}' AND \"DDS_DATE_CREATION\" < '{until}' "
        f"AND \"LOC_LAT\" BETWEEN '{lat_low}' AND '{lat_high}' "
        f"AND \"LOC_LONG\" BETWEEN '{lon_low}' AND '{lon_high}' "
        f'ORDER BY "DDS_DATE_CREATION" DESC LIMIT {MAX_CANDIDATES}'
    )
    result = await ckan_api.datastore_search_sql(DQ_API_URL, sql)
    records = result.get("records", [])
    items = []
    for row in records:
        try:
            plat, plon = float(row["LOC_LAT"]), float(row["LOC_LONG"])
        except (KeyError, TypeError, ValueError):
            continue
        if not (math.isfinite(plat) and math.isfinite(plon)):
            continue
        distance = haversine_m(lat, lon, plat, plon)
        if distance > radius_m:
            continue
        items.append(
            {
                "name": row.get("ACTI_NOM") or "Demande 311",
                "nature": row.get("NATURE"),
                "date": row.get("DDS_DATE_CREATION"),
                "status": row.get("DERNIER_STATUT") or "Statut non publié",
                "status_date": row.get("DATE_DERNIER_STATUT"),
                "borough": row.get("ARRONDISSEMENT_GEO"),
                "latitude": plat,
                "longitude": plon,
                "distance_m": round(distance),
            }
        )
    items.sort(key=lambda item: str(item.get("date") or ""), reverse=True)
    displayed, _ = attach_nearby_maps(items[:limit], query_lat=lat, query_lon=lon)
    return {
        "items": displayed,
        "matched_in_sample": len(items),
        "truncated": len(records) >= MAX_CANDIDATES,
        "since": since,
        "days": days,
        "through": anchor.isoformat(),
        "latest_available_date": latest_date.isoformat() if latest_date else None,
        "historical": bool(latest_date and latest_date < today - timedelta(days=7)),
        "resolved_address": resolved,
        "source": MTL_311_SOURCE_URL,
        "donnees_quebec_url": DQ_311_SOURCE_URL,
        "note": "Demandes publiées et géolocalisées seulement. Une demande ne confirme pas une intervention. "
        "Les statuts sont ceux de la source; la sélection n'est pas un décompte exhaustif.",
    }
