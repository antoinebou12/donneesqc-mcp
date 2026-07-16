"""Mapping GeoJSON ICherche (Adresses Québec) -> dicts MCP."""

from __future__ import annotations

from typing import Any

from helpers.common.maps_format import attach_maps_pin


def feature_to_geocode_result(feat: dict[str, Any]) -> dict[str, Any]:
    """Adresse + coords depuis une feature geocode."""
    props = feat.get("properties", {})
    coords = (feat.get("geometry") or {}).get("coordinates") or []
    return attach_maps_pin(
        {
            "address": props.get("recherche", props.get("nom", "")),
            "municipality": props.get("municipalite", ""),
            "mrc": props.get("mrc", ""),
            "region": props.get("region", ""),
            "longitude": coords[0] if len(coords) > 0 else None,
            "latitude": coords[1] if len(coords) > 1 else None,
            "confidence": props.get("score", None),
        }
    )


def feature_to_reverse_result(feat: dict[str, Any]) -> dict[str, Any]:
    """Adresse détaillée depuis une feature reverse geocode."""
    props = feat.get("properties", {})
    coords = (feat.get("geometry") or {}).get("coordinates") or []
    return attach_maps_pin(
        {
            "address": props.get("recherche", props.get("nom", "")),
            "street_number": props.get("numero", ""),
            "street": props.get("rue", ""),
            "municipality": props.get("municipalite", ""),
            "mrc": props.get("mrc", ""),
            "region": props.get("region", ""),
            "postal_code": props.get("codePostal", ""),
            "longitude": coords[0] if len(coords) > 0 else None,
            "latitude": coords[1] if len(coords) > 1 else None,
            "distance_m": props.get("distance", None),
        }
    )
