"""Client DataStore SIT Québec — nearby multi-catégories (CSV aperçu)."""

from __future__ import annotations

import asyncio
import math
from typing import Any, Literal

from helpers.common import ckan_api
from helpers.common.config import DQ_API_URL
from helpers.common.maps_format import attach_nearby_maps
from helpers.common.urls import dq_dataset_url
from helpers.mtl.geo import haversine_m, validate_wgs84
from helpers.mtl.nearby import resolve_user_point

SitCategory = Literal[
    "restauration",
    "culture",
    "hotels",
    "loisirs",
    "nature",
]

_MAX_NEARBY = 50
_MAX_BBOX_CANDIDATES = 5000
_MIN_RADIUS_M = 50.0
_MAX_RADIUS_M = 15000.0

# Official Tourisme Québec caveat for the tabular CSV export.
SIT_CSV_NOTE = (
    "Aperçu SIT Québec (CSV) — ne recense pas l'offre touristique dans sa totalité. "
    "Les données sont multi-dimensionnelles ; pour un export plus complet, "
    "préférer les ressources service web du jeu sur Données Québec. "
    "Contact diffuseur : donnees@tourisme.gouv.qc.ca"
)

# Resource IDs from Données Québec DataStore (CSV active).
SIT_CATEGORIES: dict[str, dict[str, str]] = {
    "restauration": {
        "dataset_id": "sit-quebec-restauration",
        "resource_id": "64d52e5a-5cc5-40ce-a0c4-96c318087e97",
        "label": "Restauration",
    },
    "culture": {
        "dataset_id": "sit-quebec-culture-art-et-patrimoine",
        "resource_id": "f0bf3291-0a9e-4133-a0c5-01c148eab9d2",
        "label": "Culture, art et patrimoine",
    },
    "hotels": {
        "dataset_id": "sit-quebec-hotels",
        "resource_id": "8ea2fd71-b4e7-4cef-95fc-c36d4a0c44d3",
        "label": "Hôtels / hébergement",
    },
    "loisirs": {
        "dataset_id": "sit-quebec-divertissements-et-loisirs",
        "resource_id": "5b9ec554-6cfc-4559-8715-c9212cc2c44e",
        "label": "Divertissements et loisirs",
    },
    "nature": {
        "dataset_id": "sit-quebec-nature-sports-et-plein-air",
        "resource_id": "fe020f80-c2b8-487a-ab92-13b0080b7ca4",
        "label": "Nature, sports et plein air",
    },
}

_COMMON_SQL_FIELDS = (
    '"IdentifiantUnique"',
    '"NomEtablissement"',
    '"TypeEtablissement"',
    '"NumeroVoie"',
    '"Municipalite"',
    '"CodePostal"',
    '"Latitude"',
    '"Longitude"',
    '"TelephonePrincipal"',
    '"SiteInternet"',
)

_RESTO_EXTRA = (
    '"CuisineOrigine"',
    '"CuisineTypeSpecialite"',
)

_HOTEL_TYPE_FIELD = '"CategorieEtablissementHebergementTouristique"'


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bbox(
    latitude: float,
    longitude: float,
    radius_m: float,
) -> tuple[float, float, float, float]:
    lat_delta = radius_m / 111_320.0
    cos_lat = max(0.2, abs(math.cos(math.radians(latitude))))
    lon_delta = radius_m / (111_320.0 * cos_lat)
    return (
        latitude - lat_delta,
        latitude + lat_delta,
        longitude - lon_delta,
        longitude + lon_delta,
    )


def normalize_place(raw: dict[str, Any], *, category: str) -> dict[str, Any]:
    """Map a SIT DataStore row to a slim place dict."""
    lat = _to_float(raw.get("Latitude") if "Latitude" in raw else raw.get("latitude"))
    lon = _to_float(raw.get("Longitude") if "Longitude" in raw else raw.get("longitude"))
    street = str(raw.get("NumeroVoie") or "").strip() or None
    city = str(raw.get("Municipalite") or "").strip() or None
    postal = str(raw.get("CodePostal") or "").strip() or None
    address_parts = [p for p in (street, city, postal) if p]
    address = ", ".join(address_parts) if address_parts else None

    place_type = str(raw.get("TypeEtablissement") or "").strip() or None
    if not place_type and category == "hotels":
        place_type = str(raw.get("CategorieEtablissementHebergementTouristique") or "").strip() or None

    cuisine = str(raw.get("CuisineOrigine") or "").strip() or None
    specialty = str(raw.get("CuisineTypeSpecialite") or "").strip() or None
    if cuisine and specialty and specialty.casefold() not in cuisine.casefold():
        cuisine_label = f"{cuisine} — {specialty}"
    else:
        cuisine_label = cuisine or specialty

    return {
        "id": str(raw.get("IdentifiantUnique") or "").strip() or None,
        "name": str(raw.get("NomEtablissement") or "").strip() or None,
        "type": place_type,
        "category": category,
        "cuisine": cuisine_label,
        "address": address,
        "phone": str(raw.get("TelephonePrincipal") or "").strip() or None,
        "web": str(raw.get("SiteInternet") or "").strip() or None,
        "latitude": lat,
        "longitude": lon,
    }


def normalize_restaurant(raw: dict[str, Any]) -> dict[str, Any]:
    """Backward-compatible alias for restauration rows."""
    return normalize_place(raw, category="restauration")


def _sql_fields(category: str) -> str:
    fields = list(_COMMON_SQL_FIELDS)
    if category == "restauration":
        fields.extend(_RESTO_EXTRA)
    elif category == "hotels":
        fields.append(_HOTEL_TYPE_FIELD)
        # Hotels schema may omit TypeEtablissement — keep Nom only if missing
        if '"TypeEtablissement"' in fields:
            # still fine if column missing? SQL would fail. Hotels sample had NomEtablissement
            # but not TypeEtablissement — remove it for hotels.
            fields = [f for f in fields if f != '"TypeEtablissement"']
    return ", ".join(fields)


async def _list_category_nearby(
    *,
    category: str,
    lat: float,
    lon: float,
    radius_m: float,
    limit: int,
) -> dict[str, Any]:
    meta = SIT_CATEGORIES[category]
    resource_id = meta["resource_id"]
    dataset_id = meta["dataset_id"]
    lat_min, lat_max, lon_min, lon_max = _bbox(lat, lon, float(radius_m))
    fields = _sql_fields(category)
    sql = (
        f'SELECT {fields} FROM "{resource_id}" '  # noqa: S608
        f'WHERE "Latitude"::float >= {lat_min} AND "Latitude"::float <= {lat_max} '
        f'AND "Longitude"::float >= {lon_min} AND "Longitude"::float <= {lon_max} '
        f"LIMIT {_MAX_BBOX_CANDIDATES}"
    )
    result = await ckan_api.datastore_search_sql(DQ_API_URL, sql)
    nearby: list[dict[str, Any]] = []
    for raw in result.get("records", []):
        item = normalize_place(raw, category=category)
        plat = item.get("latitude")
        plon = item.get("longitude")
        if plat is None or plon is None:
            continue
        distance = haversine_m(lat, lon, float(plat), float(plon))
        if distance <= float(radius_m):
            nearby.append({**item, "distance_m": round(distance, 1)})
    nearby.sort(key=lambda r: r["distance_m"])
    places, nearest_directions = attach_nearby_maps(
        nearby[:limit],
        query_lat=lat,
        query_lon=lon,
    )
    portal = dq_dataset_url(dataset_id)
    return {
        "category": category,
        "label": meta["label"],
        "total": len(nearby),
        "places": places,
        "nearest_google_maps_directions_url": nearest_directions,
        "source": portal,
        "dataset_id": dataset_id,
        "resource_id": resource_id,
        "note": SIT_CSV_NOTE,
    }


async def list_nearby(
    *,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 500.0,
    limit: int = 15,
    category: SitCategory = "restauration",
) -> dict[str, Any]:
    """Places SIT dans un rayon (bbox SQL + haversine). Défaut: restauration."""
    cat = (category or "restauration").strip().lower()
    if cat not in SIT_CATEGORIES:
        msg = f"category doit etre l'un de: {', '.join(sorted(SIT_CATEGORIES))}."
        raise ValueError(msg)

    loc = await resolve_user_point(
        address=address,
        latitude=latitude,
        longitude=longitude,
        allow_client_ip=True,
    )
    lat = float(loc["latitude"])
    lon = float(loc["longitude"])
    validate_wgs84(lat, lon)

    if not (_MIN_RADIUS_M <= float(radius_m) <= _MAX_RADIUS_M):
        msg = f"radius_m doit etre entre {_MIN_RADIUS_M:g} et {_MAX_RADIUS_M:g}."
        raise ValueError(msg)
    lim = max(1, min(int(limit), _MAX_NEARBY))

    data = await _list_category_nearby(
        category=cat,
        lat=lat,
        lon=lon,
        radius_m=float(radius_m),
        limit=lim,
    )
    # Keep restaurants key for restauration (backward compatible tool JSON).
    payload: dict[str, Any] = {
        "query": {
            "address": address,
            "resolved_address": loc.get("resolved_address"),
            "latitude": lat,
            "longitude": lon,
            "radius_m": float(radius_m),
            "location_source": loc.get("location_source"),
            "limit": lim,
            "category": cat,
        },
        "total": data["total"],
        "nearest_google_maps_directions_url": data["nearest_google_maps_directions_url"],
        "source": data["source"],
        "dataset_id": data["dataset_id"],
        "resource_id": data["resource_id"],
        "note": SIT_CSV_NOTE,
    }
    if cat == "restauration":
        payload["restaurants"] = data["places"]
    else:
        payload["places"] = data["places"]
    return payload


async def list_tourist_nearby(
    *,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 500.0,
    limit_per_category: int = 8,
    categories: list[str] | None = None,
) -> dict[str, Any]:
    """Fan-out SIT: restauration + culture + hotels + loisirs (+ nature optionnel)."""
    loc = await resolve_user_point(
        address=address,
        latitude=latitude,
        longitude=longitude,
        allow_client_ip=True,
    )
    lat = float(loc["latitude"])
    lon = float(loc["longitude"])
    validate_wgs84(lat, lon)
    if not (_MIN_RADIUS_M <= float(radius_m) <= _MAX_RADIUS_M):
        msg = f"radius_m doit etre entre {_MIN_RADIUS_M:g} et {_MAX_RADIUS_M:g}."
        raise ValueError(msg)
    lim = max(1, min(int(limit_per_category), _MAX_NEARBY))
    cats = categories or ["restauration", "culture", "hotels", "loisirs"]
    for c in cats:
        if c not in SIT_CATEGORIES:
            msg = f"category inconnue: {c}"
            raise ValueError(msg)

    results = await asyncio.gather(
        *[
            _list_category_nearby(
                category=c,
                lat=lat,
                lon=lon,
                radius_m=float(radius_m),
                limit=lim,
            )
            for c in cats
        ],
        return_exceptions=True,
    )

    by_category: dict[str, Any] = {}
    merged: list[dict[str, Any]] = []
    errors: dict[str, str] = {}
    for cat, result in zip(cats, results, strict=True):
        if isinstance(result, BaseException):
            errors[cat] = str(result) or result.__class__.__name__
            continue
        by_category[cat] = result
        merged.extend(result.get("places") or [])

    merged.sort(key=lambda r: r.get("distance_m") or 0)
    top, nearest = attach_nearby_maps(
        merged[: max(lim * 2, lim)],
        query_lat=lat,
        query_lon=lon,
    )
    return {
        "query": {
            "address": address,
            "resolved_address": loc.get("resolved_address"),
            "latitude": lat,
            "longitude": lon,
            "radius_m": float(radius_m),
            "location_source": loc.get("location_source"),
            "limit_per_category": lim,
            "categories": cats,
        },
        "total": len(merged),
        "places": top,
        "by_category": {
            k: {
                "total": v.get("total"),
                "label": v.get("label"),
                "source": v.get("source"),
                "places": v.get("places"),
            }
            for k, v in by_category.items()
        },
        "errors": errors or None,
        "nearest_google_maps_directions_url": nearest,
        "note": SIT_CSV_NOTE,
        "source": dq_dataset_url("sit-quebec-restauration"),
    }
