"""Client iCherche (Adresses Québec) â€” geocode / reverse partagés."""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx

from helpers.common.config import GEOCODER_URL
from helpers.common.http_client import fetch_json

logger = logging.getLogger(__name__)

# Ex.: "275 Rue Notre-Dame Est, Montréal H2Y1C6"
_CIVIC_LABEL_RE = re.compile(
    r"^(\d+[A-Za-z]?)\s+(.+?),\s*.*?"
    r"([A-Za-z]\d[A-Za-z])\s*(\d[A-Za-z]\d)\s*$",
    re.UNICODE,
)

_REVERSE_ERROR = (
    "Geocodage inverse iCherche indisponible pour ({lat}, {lon}). "
    "Passez une adresse civique (parametre address) plutot que latitude/longitude."
)


async def geocode_features(q: str, *, limit: int = 1) -> list[dict[str, Any]]:
    """GET /geocode avec geometry=true (sinon iCherche omet les coordonnees)."""
    cleaned = (q or "").strip()
    if not cleaned:
        msg = "Le parametre d'adresse est requis."
        raise ValueError(msg)
    size = max(1, min(int(limit), 10))
    data = await fetch_json(
        f"{GEOCODER_URL}/geocode",
        params={
            "q": cleaned,
            "limit": size,
            "type": "adresses",
            "geometry": "true",
        },
    )
    features = data.get("features") or []
    if not isinstance(features, list):
        return []
    return [f for f in features if isinstance(f, dict)]


async def reverse_features(
    latitude: float,
    longitude: float,
    *,
    limit: int = 1,
) -> list[dict[str, Any]]:
    """GET /reverse â€” essaie un parametre alternatif si HTTP 400."""
    size = max(1, min(int(limit), 5))
    loc = f"{longitude},{latitude}"
    attempts: list[dict[str, Any]] = [
        {"loc": loc, "limit": size, "type": "adresses"},
        {"loc": loc, "limit": size, "type": "adresses", "geometry": "true"},
        {"loc": loc, "limit": size, "type": "adresse"},
    ]
    last_error: Exception | None = None
    for params in attempts:
        try:
            data = await fetch_json(
                f"{GEOCODER_URL}/reverse",
                params=params,
                use_cache=False,
            )
        except httpx.HTTPStatusError as exc:
            last_error = exc
            logger.warning(
                "iCherche reverse HTTP %s params=%s",
                exc.response.status_code,
                params,
            )
            continue
        features = data.get("features") or []
        if isinstance(features, list) and features:
            return [f for f in features if isinstance(f, dict)]
        last_error = ValueError("aucune feature")
    msg = _REVERSE_ERROR.format(lat=latitude, lon=longitude)
    raise ValueError(msg) from last_error


def parse_civic_from_label(nom: str) -> dict[str, str]:
    """Extrait numero / rue / code postal depuis un libelle iCherche ``nom``."""
    cleaned = " ".join((nom or "").split()).strip()
    if not cleaned:
        return {"street_number": "", "street": "", "postal_code": ""}
    match = _CIVIC_LABEL_RE.match(cleaned)
    if not match:
        return {"street_number": "", "street": "", "postal_code": ""}
    number, street, pc1, pc2 = match.groups()
    return {
        "street_number": number.strip(),
        "street": street.strip(),
        "postal_code": f"{pc1.upper()} {pc2.upper()}",
    }
