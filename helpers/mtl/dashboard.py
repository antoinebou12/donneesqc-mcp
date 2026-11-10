"""Compose existing Montréal tools with bounded, independent failures."""

import asyncio
import json
from datetime import UTC, datetime

from helpers.common.maps_format import openstreetmap_embed_url, openstreetmap_url
from helpers.mtl.nearby import resolve_point

_ROW_KEYS = frozenset(
    [
        "id",
        "name",
        "nom",
        "titre",
        "title",
        "stop_name",
        "stop_code",
        "emplacement",
        "street",
        "description",
        "latitude",
        "longitude",
        "nearest_lat",
        "nearest_lon",
        "distance_m",
        "num_bikes_available",
        "date",
        "status",
        "status_date",
        "nature",
        "borough",
        "toponyme",
        "arrondissement",
        "type_pay",
        "heures",
        "nbr_places",
        "note_fr",
        "starttime",
        "endtime",
        "type",
        "cuisine",
        "artiste",
        "annee",
        "nom_ecocentre",
        "start",
        "end",
        "place",
        "url",
        "google_maps_url",
        "openstreetmap_url",
        "google_calendar_url",
        "source_url",
    ]
)
_ROW_LISTS = frozenset(
    [
        "items",
        "parks",
        "stations",
        "stops",
        "restrictions",
        "lots",
        "entraves",
        "restaurants",
        "places",
        "alerts",
        "murals",
        "ecocentres",
    ]
)


def _compact_section(data: dict) -> dict:
    """Keep displayed rows and citations while removing duplicated presentations."""
    out = {k: v for k, v in data.items() if k not in {"calendar_md", "calendar_ascii", "presentation_md"}}
    if "parks" in out:
        out.pop("items", None)
    if "items" in out:
        out.pop("entraves", None)
    if "by_category" in out:
        out.pop("places", None)
        out["by_category"] = {k: _compact_section(v) for k, v in out["by_category"].items()}
    for key in _ROW_LISTS & out.keys():
        if isinstance(out[key], list):
            out[key] = [{k: v for k, v in row.items() if k in _ROW_KEYS} for row in out[key] if isinstance(row, dict)]
    return out


async def build_dashboard(address: str, radius_m: int, view: str = "all") -> dict:
    """Resolve one location and retain each tool's citations and data."""
    from tools.mtl.avis.find_avis_nearby import find_avis_nearby
    from tools.mtl.bixi.find_bixi_nearby import find_bixi_nearby
    from tools.mtl.collecte.find_montreal_ecocentres import find_montreal_ecocentres
    from tools.mtl.entraves.find_entraves_nearby import find_entraves_nearby
    from tools.mtl.events.events_soon import events_soon_tool
    from tools.mtl.murales.list_murales_nearby import list_murales_nearby
    from tools.mtl.parcs.find_parcs_nearby import find_parcs_nearby
    from tools.mtl.parking.find_parking_deneigement_nearby import find_parking_deneigement_nearby
    from tools.mtl.parking.find_restrictions_nearby import find_parking_restrictions_nearby
    from tools.mtl.rem.find_stops_nearby import find_rem_stops_nearby
    from tools.mtl.requests311 import requests311_nearby
    from tools.mtl.stm.find_stops_nearby import find_stm_stops_nearby
    from tools.mtl.weather.find_weather_nearby import find_weather_nearby
    from tools.qc.sit.restaurants_nearby import qc_sit_restaurants_nearby, qc_sit_tourist_nearby

    address = address.strip()
    if not address or len(address) > 300:
        raise ValueError("Saisissez un lieu de 1 à 300 caractères.")
    if not 100 <= radius_m <= 3000:
        raise ValueError("Le rayon doit être compris entre 100 et 3000 mètres.")
    if view not in {"all", "daily", "move", "out"}:
        raise ValueError("Vue inconnue : all, daily, move, out.")
    lookup = "275 rue Notre-Dame Est, Montréal" if address == "Hôtel de Ville de Montréal" else address
    async with asyncio.timeout(20):
        lat, lon, resolved = await resolve_point(address=lookup, latitude=None, longitude=None, allow_client_ip=False)
    if not (45.3 <= lat <= 45.8 and -74.1 <= lon <= -73.4):
        raise ValueError("Choisissez un lieu dans la région de Montréal.")
    point = {"latitude": lat, "longitude": lon}

    async def section(
        fn, nearby: bool, extra: dict | None = None, *, expand_empty: bool = False, latlng: bool = False
    ) -> dict:
        try:
            async with asyncio.timeout(25):
                args = {
                    **({"lat": lat, "lng": lon} if latlng else point),
                    **({"radius_m": radius_m, "limit": 6} if nearby else {}),
                    **(extra or {}),
                }
                raw = await fn(**args)
                data = json.loads(raw)
                if expand_empty and not data.get("error") and not data.get("lots"):
                    raw = await fn(**{**args, "radius_m": 5000})
                    data = json.loads(raw)
                    data["expanded_from_radius_m"] = radius_m
                    data["search_radius_m"] = 5000
        except (TimeoutError, ValueError, OSError):
            return {"error": "Source indisponible. Réessayez dans quelques instants."}
        else:
            return _compact_section(data)

    keys = (
        "weather",
        "bixi",
        "parks",
        "stm",
        "requests311",
        "parking",
        "snowparking",
        "roadworks",
        "restaurants",
        "tourism",
        "avis",
        "murals",
        "rem",
        "ecocentres",
        "events",
    )
    results = await asyncio.gather(
        section(find_weather_nearby, False),
        section(find_bixi_nearby, True),
        section(find_parcs_nearby, True),
        section(find_stm_stops_nearby, True),
        section(requests311_nearby, True, {"use_latest_available": True}),
        section(find_parking_restrictions_nearby, True),
        section(find_parking_deneigement_nearby, True, expand_empty=True),
        section(find_entraves_nearby, True),
        section(qc_sit_restaurants_nearby, True),
        section(qc_sit_tourist_nearby, False, {"radius_m": radius_m, "limit_per_category": 3}),
        section(find_avis_nearby, True),
        section(list_murales_nearby, True),
        section(find_rem_stops_nearby, True),
        section(find_montreal_ecocentres, False, {"limit": 3}, latlng=True),
        section(events_soon_tool, False, {"hours": 168, "limit": 6}),
    )
    return {
        "address": resolved or address,
        "query": address,
        "latitude": lat,
        "longitude": lon,
        "radius_m": radius_m,
        "view": view,
        "openstreetmap_url": openstreetmap_url(lat, lon),
        "openstreetmap_embed_url": openstreetmap_embed_url(lat, lon, radius_m),
        "retrieved_at": datetime.now(UTC).isoformat(),
        "sections": dict(zip(keys, results, strict=True)),
    }
