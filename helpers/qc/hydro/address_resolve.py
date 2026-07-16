"""Résolution d'adresse / coordonnées → champs civiques pour Info-pannes."""

from __future__ import annotations

import re
from typing import Any

from helpers.qc.geo.icherche_client import (
    geocode_features,
    parse_civic_from_label,
    reverse_features,
)

_POSTAL_RE = re.compile(r"^([A-Z]\d[A-Z])\s*(\d[A-Z]\d)$", re.IGNORECASE)


def normalize_postal_code(value: str) -> str:
    """Normalise un code postal canadien en ``A1A 1A1``."""
    cleaned = (value or "").strip().upper().replace("\u00a0", " ")
    cleaned = re.sub(r"\s+", "", cleaned)
    match = _POSTAL_RE.match(cleaned)
    if not match:
        return (value or "").strip()
    return f"{match.group(1).upper()} {match.group(2).upper()}"


def feature_to_civic(feat: dict[str, Any]) -> dict[str, Any]:
    """Extrait les champs civiques depuis une feature iCherche."""
    props = feat.get("properties") or {}
    coords = (feat.get("geometry") or {}).get("coordinates") or []
    civic = {
        "street_number": str(props.get("numero") or "").strip(),
        "street": str(props.get("rue") or "").strip(),
        "postal_code": normalize_postal_code(str(props.get("codePostal") or "")),
        "municipality": str(props.get("municipalite") or "").strip(),
        "address": str(props.get("recherche") or props.get("nom") or "").strip(),
        "longitude": coords[0] if len(coords) > 0 else None,
        "latitude": coords[1] if len(coords) > 1 else None,
    }
    # Features sparses : uniquement ``nom`` + code postal dans le libelle.
    if not civic["street_number"] or not civic["street"] or not civic["postal_code"]:
        parsed = parse_civic_from_label(str(props.get("nom") or civic["address"]))
        if not civic["street_number"]:
            civic["street_number"] = parsed["street_number"]
        if not civic["street"]:
            civic["street"] = parsed["street"]
        if not civic["postal_code"]:
            civic["postal_code"] = normalize_postal_code(parsed["postal_code"])
    return civic


def _require_civic(civic: dict[str, Any], *, context: str) -> dict[str, Any]:
    if not civic.get("street_number") or not civic.get("street"):
        msg = f"Adresse incomplete apres geocodage ({context}): numero ou rue manquant."
        raise ValueError(msg)
    if not civic.get("postal_code") or " " not in str(civic["postal_code"]):
        msg = f"Code postal manquant ou invalide apres geocodage ({context}). Info-pannes exige le format A1A 1A1."
        raise ValueError(msg)
    return civic


def _merge_civic(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in extra.items():
        if value in (None, ""):
            continue
        if not merged.get(key):
            merged[key] = value
    return merged


async def resolve_from_address(address: str) -> dict[str, Any]:
    """Geocode une adresse libre → champs civiques."""
    cleaned = address.strip()
    if not cleaned:
        msg = "Le parametre 'address' est requis."
        raise ValueError(msg)
    features = await geocode_features(cleaned, limit=1)
    if not features:
        msg = f"Adresse introuvable: '{cleaned}'."
        raise ValueError(msg)
    civic = feature_to_civic(features[0])
    # Completer via reverse seulement si champs encore manquants et coords ok.
    if (not civic.get("postal_code") or not civic.get("street_number")) and (
        civic.get("latitude") is not None and civic.get("longitude") is not None
    ):
        try:
            rev = await reverse_features(float(civic["latitude"]), float(civic["longitude"]))
            if rev:
                civic = _merge_civic(civic, feature_to_civic(rev[0]))
        except ValueError:
            pass
    return _require_civic(civic, context=cleaned)


async def resolve_from_coords(latitude: float, longitude: float) -> dict[str, Any]:
    """Reverse-geocode lat/lng → champs civiques."""
    features = await reverse_features(latitude, longitude, limit=1)
    if not features:
        msg = f"Aucune adresse trouvee pour ({latitude}, {longitude})."
        raise ValueError(msg)
    return _require_civic(feature_to_civic(features[0]), context=f"{latitude},{longitude}")


async def resolve_civic(
    *,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict[str, Any]:
    """Resolve soit une adresse, soit un couple lat/lng."""
    has_address = bool(address and address.strip())
    has_lat = latitude is not None
    has_lon = longitude is not None
    if has_lat != has_lon:
        msg = "Les parametres latitude et longitude doivent etre fournis ensemble."
        raise ValueError(msg)
    if has_address and (has_lat or has_lon):
        msg = "Fournir soit 'address', soit latitude+longitude - pas les deux."
        raise ValueError(msg)
    if not has_address and not (has_lat and has_lon):
        msg = "Fournir 'address' ou latitude+longitude."
        raise ValueError(msg)
    if has_address:
        return await resolve_from_address(address or "")
    return await resolve_from_coords(float(latitude), float(longitude))  # type: ignore[arg-type]
