"""STM GTFS-RT (positions / arrivées) et i3 (état du service)."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from google.transit import gtfs_realtime_pb2

from helpers.common.config import (
    DEFAULT_TIMEZONE,
    STM_API_KEY,
    STM_DEVELOPERS_PORTAL_URL,
    STM_SERVICE_ALERTS_URL,
    STM_TRIP_UPDATES_URL,
    STM_VEHICLE_POSITIONS_URL,
)
from helpers.common.http_client import fetch_bytes, fetch_json
from helpers.common.maps_format import attach_nearby_maps
from helpers.mtl.geo import haversine_m
from helpers.mtl.stm_gtfs import filter_stops_nearby, get_stop, load_stops

_MIN_RADIUS_M = 50.0
_MAX_RADIUS_M = 5000.0
_MAX_LIMIT = 50
_MAX_ARRIVALS = 30
_MAX_VEHICLES = 100

_MISSING_KEY_MSG = (
    f"STM_API_KEY manquante. Obtenez une clé gratuite sur {STM_DEVELOPERS_PORTAL_URL} puis définissez STM_API_KEY."
)


def require_api_key() -> str:
    """Return STM API key or raise ValueError with setup hint."""
    key = (STM_API_KEY or "").strip()
    if not key:
        raise ValueError(_MISSING_KEY_MSG)
    return key


def _rt_headers(api_key: str) -> dict[str, str]:
    return {
        "apiKey": api_key,
        "Accept": "application/x-protobuf",
    }


def _i3_headers(api_key: str) -> dict[str, str]:
    return {"apiKey": api_key, "Accept": "application/json"}


def parse_feed_message(raw: bytes) -> gtfs_realtime_pb2.FeedMessage:
    """Decode a GTFS-RT FeedMessage protobuf."""
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(raw)
    return feed


def parse_vehicle_positions(
    feed: gtfs_realtime_pb2.FeedMessage,
    *,
    route: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Extract vehicle rows from a vehiclePositions feed."""
    route_filter = str(route).strip() if route else None
    lim = max(1, min(int(limit), _MAX_VEHICLES))
    use_radius = latitude is not None and longitude is not None and radius_m is not None and radius_m > 0
    if use_radius and radius_m is not None and not (_MIN_RADIUS_M <= float(radius_m) <= _MAX_RADIUS_M):
        msg = f"radius_m doit etre entre {_MIN_RADIUS_M} et {_MAX_RADIUS_M}."
        raise ValueError(msg)

    vehicles: list[dict[str, Any]] = []
    for entity in feed.entity:
        if not entity.HasField("vehicle"):
            continue
        veh = entity.vehicle
        if not veh.HasField("position"):
            continue
        lat = float(veh.position.latitude)
        lon = float(veh.position.longitude)
        if lat == 0.0 and lon == 0.0:
            continue
        route_id = ""
        trip_id = ""
        if veh.HasField("trip"):
            route_id = (veh.trip.route_id or "").strip()
            trip_id = (veh.trip.trip_id or "").strip()
        if route_filter and route_id != route_filter:
            continue
        dist: float | None = None
        if use_radius and latitude is not None and longitude is not None and radius_m is not None:
            dist = haversine_m(float(latitude), float(longitude), lat, lon)
            if dist > float(radius_m):
                continue
        vehicle_id = ""
        if veh.HasField("vehicle"):
            vehicle_id = (veh.vehicle.id or veh.vehicle.label or "").strip()
        row: dict[str, Any] = {
            "vehicle_id": vehicle_id or entity.id,
            "route_id": route_id or None,
            "trip_id": trip_id or None,
            "latitude": lat,
            "longitude": lon,
            "bearing": float(veh.position.bearing) if veh.position.HasField("bearing") else None,
            "speed": float(veh.position.speed) if veh.position.HasField("speed") else None,
            "timestamp": int(veh.timestamp) if veh.timestamp else None,
            "occupancy_status": int(veh.occupancy_status) if veh.HasField("occupancy_status") else None,
        }
        if dist is not None:
            row["distance_m"] = round(dist, 1)
        vehicles.append(row)

    if use_radius:
        vehicles.sort(key=lambda r: r.get("distance_m", 0.0))
    return vehicles[:lim]


def _arrival_epoch(stu: Any) -> int | None:
    if stu.HasField("arrival") and stu.arrival.time:
        return int(stu.arrival.time)
    if stu.HasField("departure") and stu.departure.time:
        return int(stu.departure.time)
    return None


def _format_local(epoch: int, tz_name: str) -> str:
    tz = ZoneInfo(tz_name)
    return datetime.fromtimestamp(epoch, tz=UTC).astimezone(tz).strftime("%Y-%m-%d %H:%M:%S %Z")


def parse_arrivals_for_stop(
    feed: gtfs_realtime_pb2.FeedMessage,
    stop_id: str,
    *,
    limit: int = 15,
    timezone: str = DEFAULT_TIMEZONE,
    now_epoch: int | None = None,
) -> list[dict[str, Any]]:
    """Extract upcoming arrivals at stop_id from tripUpdates."""
    sid = str(stop_id).strip()
    if not sid:
        msg = "stop_id est requis."
        raise ValueError(msg)
    lim = max(1, min(int(limit), _MAX_ARRIVALS))
    now = int(now_epoch if now_epoch is not None else time.time())
    arrivals: list[dict[str, Any]] = []

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue
        tu = entity.trip_update
        route_id = (tu.trip.route_id or "").strip() if tu.HasField("trip") else ""
        trip_id = (tu.trip.trip_id or "").strip() if tu.HasField("trip") else ""
        for stu in tu.stop_time_update:
            if (stu.stop_id or "").strip() != sid:
                continue
            arrival_time = _arrival_epoch(stu)
            if arrival_time is None or arrival_time < now - 60:
                continue
            delay = None
            if stu.HasField("arrival") and stu.arrival.HasField("delay"):
                delay = int(stu.arrival.delay)
            elif stu.HasField("departure") and stu.departure.HasField("delay"):
                delay = int(stu.departure.delay)
            dep = int(stu.departure.time) if stu.HasField("departure") and stu.departure.time else None
            arrivals.append(
                {
                    "trip_id": trip_id or None,
                    "route_id": route_id or None,
                    "stop_id": sid,
                    "arrival_time": arrival_time,
                    "arrival_local": _format_local(arrival_time, timezone),
                    "departure_time": dep,
                    "departure_local": _format_local(dep, timezone) if dep else None,
                    "delay_seconds": delay,
                }
            )

    arrivals.sort(key=lambda r: r["arrival_time"])
    return arrivals[:lim]


def parse_service_alerts(
    payload: dict[str, Any] | list[Any],
    *,
    alert_type: str = "all",
) -> list[dict[str, Any]]:
    """Normalize i3 etatservice JSON into a flat alerts list."""
    wanted = (alert_type or "all").strip().lower()
    if wanted not in {"all", "metro", "bus", "train"}:
        msg = "type doit etre metro, bus, train ou all."
        raise ValueError(msg)

    raw_items: list[Any]
    if isinstance(payload, list):
        raw_items = payload
    elif isinstance(payload, dict):
        for key in ("alerts", "Alerts", "lignes", "Lignes", "results", "data"):
            val = payload.get(key)
            if isinstance(val, list):
                raw_items = val
                break
        else:
            # STM i3 often returns {metro: [...], bus: [...], train: [...]}
            raw_items = []
            for key in ("metro", "bus", "train"):
                val = payload.get(key)
                if isinstance(val, list):
                    for entry in val:
                        if isinstance(entry, dict):
                            raw_items.append({**entry, "_alert_type": key})
                        else:
                            raw_items.append(entry)
            if not raw_items:
                raw_items = [payload]
    else:
        raw_items = []

    alerts: list[dict[str, Any]] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        atype = (
            str(item.get("_alert_type") or item.get("type") or item.get("Type") or item.get("category") or "")
            .strip()
            .lower()
        )
        if wanted != "all" and atype and atype != wanted:
            continue
        if wanted != "all" and not atype:
            # Nested already filtered when building from metro/bus/train keys
            pass
        messages = item.get("messages") or item.get("Messages") or item.get("message")
        if messages is None:
            messages = []
        if isinstance(messages, dict):
            messages = [messages]
        if not isinstance(messages, list):
            messages = [messages]
        alerts.append(
            {
                "id": str(item.get("id") or item.get("Id") or item.get("code") or "") or None,
                "name": item.get("name") or item.get("Name") or item.get("ligne") or item.get("title"),
                "short_name": item.get("short_name") or item.get("ShortName") or item.get("route_id"),
                "type": atype or wanted if wanted != "all" else (atype or None),
                "messages": messages,
            }
        )
    return alerts


async def fetch_vehicle_feed() -> gtfs_realtime_pb2.FeedMessage:
    key = require_api_key()
    raw = await fetch_bytes(STM_VEHICLE_POSITIONS_URL, headers=_rt_headers(key))
    return parse_feed_message(raw)


async def fetch_trip_updates_feed() -> gtfs_realtime_pb2.FeedMessage:
    key = require_api_key()
    raw = await fetch_bytes(STM_TRIP_UPDATES_URL, headers=_rt_headers(key))
    return parse_feed_message(raw)


async def fetch_alerts_payload() -> dict[str, Any] | list[Any]:
    key = require_api_key()
    return await fetch_json(STM_SERVICE_ALERTS_URL, headers=_i3_headers(key), use_cache=True)


async def list_stops_nearby(
    *,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 400.0,
    limit: int = 15,
) -> dict[str, Any]:
    """Arrêts STM proches (index bundlé)."""
    from helpers.mtl.nearby import resolve_user_point

    loc = await resolve_user_point(address=address, latitude=latitude, longitude=longitude)
    query_lat = loc["latitude"]
    query_lon = loc["longitude"]
    stops = filter_stops_nearby(
        load_stops(),
        latitude=query_lat,
        longitude=query_lon,
        radius_m=float(radius_m),
        limit=limit,
    )
    stops, nearest_directions = attach_nearby_maps(
        stops,
        query_lat=query_lat,
        query_lon=query_lon,
    )
    return {
        "query": {
            "address": address,
            "resolved_address": loc.get("resolved_address"),
            "latitude": query_lat,
            "longitude": query_lon,
            "radius_m": radius_m,
            "location_source": loc.get("location_source"),
        },
        "total": len(stops),
        "stops": stops,
        "nearest_google_maps_directions_url": nearest_directions,
        "stop_index_count": len(load_stops()),
    }


async def list_next_arrivals(
    *,
    stop_id: str,
    limit: int = 15,
) -> dict[str, Any]:
    """Prochaines arrivées GTFS-RT pour un stop_id."""
    sid = str(stop_id).strip()
    if not sid:
        msg = "stop_id est requis."
        raise ValueError(msg)
    feed = await fetch_trip_updates_feed()
    arrivals = parse_arrivals_for_stop(feed, sid, limit=limit)
    stop = get_stop(sid)
    payload: dict[str, Any] = {
        "stop_id": sid,
        "stop_name": stop.get("stop_name") if stop else None,
        "fetched_at": int(time.time()),
        "total": len(arrivals),
        "arrivals": arrivals,
        "timezone": DEFAULT_TIMEZONE,
        "trip_updates_url": STM_TRIP_UPDATES_URL,
    }
    if stop:
        payload["latitude"] = stop["latitude"]
        payload["longitude"] = stop["longitude"]
        from helpers.common.maps_format import google_maps_url

        payload["google_maps_url"] = google_maps_url(
            latitude=stop["latitude"],
            longitude=stop["longitude"],
        )
    return payload


async def list_bus_positions(
    *,
    route: str | None = None,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 800.0,
    limit: int = 50,
) -> dict[str, Any]:
    """Positions live des bus (optionnellement filtrées par ligne / proximité)."""
    feed = await fetch_vehicle_feed()
    query_lat: float | None = None
    query_lon: float | None = None
    resolved = None
    location_source = None
    use_geo = address is not None or (latitude is not None and longitude is not None)
    if use_geo:
        from helpers.mtl.nearby import resolve_user_point

        loc = await resolve_user_point(
            address=address,
            latitude=latitude,
            longitude=longitude,
        )
        query_lat = loc["latitude"]
        query_lon = loc["longitude"]
        resolved = loc.get("resolved_address")
        location_source = loc.get("location_source")

    vehicles = parse_vehicle_positions(
        feed,
        route=route,
        latitude=query_lat,
        longitude=query_lon,
        radius_m=float(radius_m) if use_geo else None,
        limit=limit,
    )
    nearest_directions = None
    if query_lat is not None and query_lon is not None:
        vehicles, nearest_directions = attach_nearby_maps(
            vehicles,
            query_lat=query_lat,
            query_lon=query_lon,
        )
    else:
        from helpers.common.maps_format import attach_maps_pin

        vehicles = [attach_maps_pin(v) for v in vehicles]

    return {
        "query": {
            "route": route,
            "address": address,
            "resolved_address": resolved,
            "latitude": query_lat,
            "longitude": query_lon,
            "radius_m": radius_m if use_geo else None,
            "location_source": location_source,
        },
        "total": len(vehicles),
        "vehicles": vehicles,
        "nearest_google_maps_directions_url": nearest_directions,
        "vehicle_positions_url": STM_VEHICLE_POSITIONS_URL,
        "fetched_at": int(time.time()),
    }


async def list_service_alerts(*, alert_type: str = "all") -> dict[str, Any]:
    """Alertes d'état du service STM (i3)."""
    payload = await fetch_alerts_payload()
    alerts = parse_service_alerts(payload, alert_type=alert_type)
    return {
        "type": alert_type,
        "total": len(alerts),
        "alerts": alerts,
        "fetched_at": int(time.time()),
        "alerts_url": STM_SERVICE_ALERTS_URL,
    }
