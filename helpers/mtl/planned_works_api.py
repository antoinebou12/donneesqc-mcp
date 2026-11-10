"""Published work permits as a fallback for the unavailable live CIFS feed."""

import math
from datetime import datetime
from zoneinfo import ZoneInfo

from helpers.common import ckan_api
from helpers.common.config import DQ_API_URL
from helpers.common.maps_format import attach_nearby_maps
from helpers.common.urls import MTL_PLANNED_WORKS_RESOURCE_ID, MTL_PLANNED_WORKS_SOURCE_URL
from helpers.mtl.geo import haversine_m


async def list_nearby(latitude: float, longitude: float, radius_m: float, limit: int, active_only: bool) -> dict:
    """Return permits whose published date range includes today, when requested."""
    dy = radius_m / 111_320
    dx = dy / max(0.2, abs(math.cos(math.radians(latitude))))
    lat_low, lat_high = sorted((str(latitude - dy), str(latitude + dy)))
    lon_low, lon_high = sorted((str(longitude - dx), str(longitude + dx)))
    today = datetime.now(ZoneInfo("America/Toronto")).date().isoformat()
    dates = (
        f"AND \"duration_start_date\" < '{today}T23:59:59' AND \"duration_end_date\" >= '{today}' "
        if active_only
        else ""
    )
    sql = (
        'SELECT "id", "occupancy_name", "reason_category", "currentstatus", "boroughid", '  # noqa: S608
        '"duration_start_date", "duration_end_date", "load_date", "latitude", "longitude" '
        f'FROM "{MTL_PLANNED_WORKS_RESOURCE_ID}" '
        f"WHERE \"latitude\" BETWEEN '{lat_low}' AND '{lat_high}' "
        f"AND \"longitude\" BETWEEN '{lon_low}' AND '{lon_high}' "
        f'{dates}ORDER BY "duration_end_date" ASC LIMIT 2000'
    )
    data = await ckan_api.datastore_search_sql(DQ_API_URL, sql)
    items = []
    for row in data.get("records", []):
        try:
            lat, lon = float(row["latitude"]), float(row["longitude"])
        except (TypeError, KeyError, ValueError):
            continue
        if not (math.isfinite(lat) and math.isfinite(lon)):
            continue
        distance = haversine_m(latitude, longitude, lat, lon)
        if distance <= radius_m:
            items.append(
                {
                    "id": row.get("id"),
                    "name": row.get("occupancy_name"),
                    "street": row.get("occupancy_name"),
                    "description": row.get("reason_category"),
                    "status": row.get("currentstatus"),
                    "borough": row.get("boroughid"),
                    "starttime": row.get("duration_start_date"),
                    "endtime": row.get("duration_end_date"),
                    "updated_at": row.get("load_date"),
                    "latitude": lat,
                    "longitude": lon,
                    "distance_m": round(distance),
                    "type": "Travaux planifiés",
                }
            )
    items.sort(key=lambda item: item["distance_m"])
    items, directions = attach_nearby_maps(items[:limit], query_lat=latitude, query_lon=longitude)
    return {
        "items": items,
        "entraves": items,
        "total": len(items),
        "fallback": True,
        "source_url": MTL_PLANNED_WORKS_SOURCE_URL,
        "dataset_id": "vmtl-info-travaux",
        "resource_id": MTL_PLANNED_WORKS_RESOURCE_ID,
        "nearest_google_maps_directions_url": directions,
        "note": "Flux CIFS indisponible. Permis de travaux couvrant la date du jour; "
        "les plages horaires et les impacts réels peuvent varier. Source : Entraves et travaux en cours.",
    }
