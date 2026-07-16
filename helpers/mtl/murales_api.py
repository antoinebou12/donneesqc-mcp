"""Client DataStore pour les murales subventionnées de Montréal."""

from __future__ import annotations

import re
from typing import Any, Literal

from helpers.common import ckan_api
from helpers.common.config import MTL_API_URL, MURALES_RESOURCE_ID
from helpers.common.maps_format import attach_maps_pin, attach_nearby_maps
from helpers.mtl.geo import haversine_m, validate_wgs84

FacetName = Literal["artiste", "arrondissement", "annee"]

_YEAR_RE = re.compile(r"^\d{4}$")
_MAX_PAGE_SIZE = 200
_MAX_NEARBY = 100
_MAX_RANDOM = 20

_PUBLIC_FIELDS = (
    "id",
    "artiste",
    "organisme",
    "adresse",
    "annee",
    "arrondissement",
    "programme_entente",
    "latitude",
    "longitude",
    "image",
)


def _table() -> str:
    return f'"{MURALES_RESOURCE_ID}"'


def _escape_literal(value: str) -> str:
    """Escape single quotes for SQL string literals."""
    return value.replace("'", "''")


def _escape_like(value: str) -> str:
    """Sanitize user text for ILIKE (strip wildcards; escape quotes).

    Montréal DataStore rejects ``ESCAPE`` clauses (HTTP 409), so ``%`` / ``_``
    are removed instead of escaped.
    """
    cleaned = value.replace("%", "").replace("_", "")
    return _escape_literal(cleaned)


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_record(row: dict[str, Any]) -> dict[str, Any]:
    """Normalise un enregistrement DataStore pour les outils MCP."""
    image = row.get("image")
    if isinstance(image, str) and image.startswith("//"):
        image = f"https:{image}"

    murale_id = row.get("id")
    try:
        murale_id_out: int | str = int(str(murale_id))
    except (TypeError, ValueError):
        murale_id_out = murale_id if murale_id is not None else ""

    return attach_maps_pin(
        {
            "id": murale_id_out,
            "artiste": row.get("artiste") or "",
            "organisme": row.get("organisme") or "",
            "adresse": (row.get("adresse") or "").strip(),
            "annee": str(row.get("annee") or "").strip(),
            "arrondissement": row.get("arrondissement") or "",
            "programme_entente": row.get("programme_entente") or "",
            "latitude": _to_float(row.get("latitude")),
            "longitude": _to_float(row.get("longitude")),
            "image": image or "",
        }
    )


def _where_clauses(
    *,
    query: str | None = None,
    artiste: str | None = None,
    arrondissement: str | None = None,
    annee: str | None = None,
    annee_min: str | None = None,
    annee_max: str | None = None,
) -> list[str]:
    clauses: list[str] = []

    if query and query.strip():
        q = _escape_like(query.strip())
        clauses.append(
            "("
            f"artiste ILIKE '%{q}%' OR "
            f"adresse ILIKE '%{q}%' OR "
            f"arrondissement ILIKE '%{q}%' OR "
            f"organisme ILIKE '%{q}%' OR "
            f"programme_entente ILIKE '%{q}%'"
            ")"
        )
    if artiste and artiste.strip():
        a = _escape_like(artiste.strip())
        clauses.append(f"artiste ILIKE '%{a}%'")
    if arrondissement and arrondissement.strip():
        b = _escape_like(arrondissement.strip())
        clauses.append(f"arrondissement ILIKE '%{b}%'")
    if annee and annee.strip():
        year = annee.strip()
        if not _YEAR_RE.match(year):
            msg = "Le parametre annee doit etre une annee a 4 chiffres (ex: 2019)."
            raise ValueError(msg)
        clauses.append(f"annee = '{_escape_literal(year)}'")
    if annee_min and annee_min.strip():
        year = annee_min.strip()
        if not _YEAR_RE.match(year):
            msg = "Le parametre annee_min doit etre une annee a 4 chiffres."
            raise ValueError(msg)
        clauses.append(f"annee >= '{_escape_literal(year)}'")
    if annee_max and annee_max.strip():
        year = annee_max.strip()
        if not _YEAR_RE.match(year):
            msg = "Le parametre annee_max doit etre une annee a 4 chiffres."
            raise ValueError(msg)
        clauses.append(f"annee <= '{_escape_literal(year)}'")

    return clauses


def _sql_where(clauses: list[str]) -> str:
    if not clauses:
        return ""
    return " WHERE " + " AND ".join(clauses)


async def search_murales(
    *,
    query: str | None = None,
    artiste: str | None = None,
    arrondissement: str | None = None,
    annee: str | None = None,
    annee_min: str | None = None,
    annee_max: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """Recherche paginée avec filtres optionnels."""
    page = max(1, page)
    page_size = max(1, min(page_size, _MAX_PAGE_SIZE))
    offset = (page - 1) * page_size
    clauses = _where_clauses(
        query=query,
        artiste=artiste,
        arrondissement=arrondissement,
        annee=annee,
        annee_min=annee_min,
        annee_max=annee_max,
    )
    where = _sql_where(clauses)
    fields = ", ".join(_PUBLIC_FIELDS)
    table = _table()

    count_sql = f"SELECT count(*) AS n FROM {table}{where}"  # noqa: S608
    count_result = await ckan_api.datastore_search_sql(MTL_API_URL, count_sql)
    total = int(count_result.get("records", [{}])[0].get("n", 0))

    data_sql = (
        f"SELECT {fields} FROM {table}{where} "  # noqa: S608
        f"ORDER BY id::int ASC LIMIT {page_size} OFFSET {offset}"
    )
    data_result = await ckan_api.datastore_search_sql(MTL_API_URL, data_sql)
    records = [normalize_record(r) for r in data_result.get("records", [])]
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "murals": records,
    }


async def get_murale(murale_id: str | int) -> dict[str, Any] | None:
    """Retourne une murale par id, ou None."""
    mid = str(murale_id).strip()
    if not mid:
        msg = "Le parametre murale_id est requis."
        raise ValueError(msg)

    result = await ckan_api.datastore_search(
        MTL_API_URL,
        resource_id=MURALES_RESOURCE_ID,
        filters={"id": mid},
        limit=1,
    )
    records = result.get("records") or []
    if not records:
        return None
    return normalize_record(records[0])


async def list_nearby(
    *,
    latitude: float,
    longitude: float,
    radius_m: float = 1000.0,
    limit: int = 20,
) -> dict[str, Any]:
    """Murales dans un rayon (haversine côté client - SQL géo bloqué en 403)."""
    validate_wgs84(latitude, longitude)
    if radius_m <= 0:
        msg = "radius_m doit etre positif."
        raise ValueError(msg)
    limit = max(1, min(limit, _MAX_NEARBY))

    result = await ckan_api.datastore_search(
        MTL_API_URL,
        resource_id=MURALES_RESOURCE_ID,
        fields=list(_PUBLIC_FIELDS),
        limit=32000,
    )
    nearby: list[dict[str, Any]] = []
    for raw in result.get("records", []):
        murale = normalize_record(raw)
        lat = murale.get("latitude")
        lon = murale.get("longitude")
        if lat is None or lon is None:
            continue
        distance = haversine_m(latitude, longitude, lat, lon)
        if distance <= radius_m:
            nearby.append({**murale, "distance_m": round(distance, 1)})

    nearby.sort(key=lambda m: m["distance_m"])
    murals, nearest_directions = attach_nearby_maps(
        nearby[:limit],
        query_lat=latitude,
        query_lon=longitude,
    )
    return {
        "latitude": latitude,
        "longitude": longitude,
        "radius_m": radius_m,
        "total": len(nearby),
        "murals": murals,
        "nearest_google_maps_directions_url": nearest_directions,
    }


async def get_random(
    *,
    artiste: str | None = None,
    arrondissement: str | None = None,
    annee: str | None = None,
    count: int = 1,
) -> dict[str, Any]:
    """Tire une ou plusieurs murales au hasard (filtres optionnels)."""
    count = max(1, min(count, _MAX_RANDOM))
    clauses = _where_clauses(artiste=artiste, arrondissement=arrondissement, annee=annee)
    where = _sql_where(clauses)
    fields = ", ".join(_PUBLIC_FIELDS)
    sql = f"SELECT {fields} FROM {_table()}{where} ORDER BY random() LIMIT {count}"  # noqa: S608
    result = await ckan_api.datastore_search_sql(MTL_API_URL, sql)
    records = [normalize_record(r) for r in result.get("records", [])]
    return {"count": len(records), "murals": records}


async def list_facets(facet: FacetName) -> dict[str, Any]:
    """Liste les valeurs distinctes d'une facette avec compteurs."""
    if facet not in {"artiste", "arrondissement", "annee"}:
        msg = "facet doit etre 'artiste', 'arrondissement' ou 'annee'."
        raise ValueError(msg)

    sql = (
        f'SELECT "{facet}" AS value, count(*) AS n '  # noqa: S608
        f"FROM {_table()} "
        f'WHERE "{facet}" IS NOT NULL AND "{facet}" <> \'\' '
        f'GROUP BY "{facet}" '
        f"ORDER BY n DESC, value ASC"
    )
    result = await ckan_api.datastore_search_sql(MTL_API_URL, sql)
    values = [{"value": row.get("value") or "", "count": int(row.get("n") or 0)} for row in result.get("records", [])]
    return {"facet": facet, "total": len(values), "values": values}
