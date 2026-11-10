"""Météo live via Open-Meteo (pas de clé API)."""

from __future__ import annotations

from typing import Any

from helpers.common.config import DEFAULT_TIMEZONE, OPEN_METEO_FORECAST_URL
from helpers.common.http_client import fetch_json
from helpers.common.maps_format import google_maps_url
from helpers.common.urls import OPEN_METEO_ATTRIBUTION, OPEN_METEO_DOCS_URL
from helpers.mtl.nearby import resolve_point

# WMO Weather interpretation codes (Open-Meteo) -> short FR labels
_WMO_LABELS_FR: dict[int, str] = {
    0: "Ciel dégagé",
    1: "Principalement clair",
    2: "Partiellement nuageux",
    3: "Couvert",
    45: "Brouillard",
    48: "Brouillard givrant",
    51: "Bruine légère",
    53: "Bruine",
    55: "Bruine dense",
    56: "Bruine verglaçante légère",
    57: "Bruine verglaçante dense",
    61: "Pluie faible",
    63: "Pluie",
    65: "Pluie forte",
    66: "Pluie verglaçante légère",
    67: "Pluie verglaçante forte",
    71: "Neige faible",
    73: "Neige",
    75: "Neige forte",
    77: "Grains de neige",
    80: "Averses faibles",
    81: "Averses",
    82: "Averses fortes",
    85: "Averses de neige faibles",
    86: "Averses de neige fortes",
    95: "Orage",
    96: "Orage avec grêle faible",
    99: "Orage avec grêle forte",
}

_CURRENT_VARS = "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weather_code,wind_speed_10m"
_DAILY_VARS = "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum"
_FORECAST_DAYS = 3


def weather_label_fr(code: int | None) -> str:
    """French label for a WMO weather code."""
    if code is None:
        return "Inconnu"
    try:
        key = int(code)
    except (TypeError, ValueError):
        return "Inconnu"
    return _WMO_LABELS_FR.get(key, f"Code météo {key}")


def parse_open_meteo(
    raw: dict[str, Any],
    *,
    latitude: float,
    longitude: float,
    resolved_address: str | None,
    timezone_name: str,
) -> dict[str, Any]:
    """Normalize Open-Meteo forecast JSON into the shared weather payload."""
    current_raw = raw.get("current")
    if not isinstance(current_raw, dict):
        current_raw = {}
    code = current_raw.get("weather_code")
    try:
        code_i = int(code) if code is not None else None
    except (TypeError, ValueError):
        code_i = None

    current = {
        "temperature_c": current_raw.get("temperature_2m"),
        "apparent_temperature_c": current_raw.get("apparent_temperature"),
        "relative_humidity_pct": current_raw.get("relative_humidity_2m"),
        "precipitation_mm": current_raw.get("precipitation"),
        "weather_code": code_i,
        "weather_label_fr": weather_label_fr(code_i),
        "wind_speed_kmh": current_raw.get("wind_speed_10m"),
        "observed_at": current_raw.get("time"),
    }

    daily_raw = raw.get("daily")
    if not isinstance(daily_raw, dict):
        daily_raw = {}
    dates = daily_raw.get("time") or []
    codes = daily_raw.get("weather_code") or []
    tmax = daily_raw.get("temperature_2m_max") or []
    tmin = daily_raw.get("temperature_2m_min") or []
    precip = daily_raw.get("precipitation_sum") or []
    daily: list[dict[str, Any]] = []
    for i, day in enumerate(dates):
        d_code = codes[i] if i < len(codes) else None
        try:
            d_code_i = int(d_code) if d_code is not None else None
        except (TypeError, ValueError):
            d_code_i = None
        daily.append(
            {
                "date": day,
                "temp_max_c": tmax[i] if i < len(tmax) else None,
                "temp_min_c": tmin[i] if i < len(tmin) else None,
                "precipitation_sum_mm": precip[i] if i < len(precip) else None,
                "weather_code": d_code_i,
                "weather_label_fr": weather_label_fr(d_code_i),
            }
        )

    maps = google_maps_url(latitude=latitude, longitude=longitude)
    summary = _summary_line(current)
    return {
        "latitude": round(latitude, 6),
        "longitude": round(longitude, 6),
        "resolved_address": resolved_address,
        "timezone": timezone_name,
        "current": current,
        "daily": daily,
        "weather_summary": summary,
        "google_maps_url": maps,
        "source": OPEN_METEO_DOCS_URL,
        "attribution": OPEN_METEO_ATTRIBUTION,
    }


def _summary_line(current: dict[str, Any]) -> str:
    temp = current.get("temperature_c")
    label = current.get("weather_label_fr") or "?"
    if temp is None:
        return str(label)
    try:
        return f"{float(temp):.0f}°C, {label}"
    except (TypeError, ValueError):
        return f"{temp}°C, {label}"


async def get_weather_nearby(
    *,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
    forecast_days: int = _FORECAST_DAYS,
) -> dict[str, Any]:
    """Resolve point then fetch Open-Meteo current + daily forecast."""
    lat, lon, resolved = await resolve_point(
        address=address,
        latitude=latitude,
        longitude=longitude,
    )
    tz = (timezone or "").strip() or DEFAULT_TIMEZONE
    days = max(1, min(int(forecast_days), 7))
    raw = await fetch_json(
        OPEN_METEO_FORECAST_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "current": _CURRENT_VARS,
            "daily": _DAILY_VARS,
            "timezone": tz,
            "forecast_days": days,
            "wind_speed_unit": "kmh",
        },
    )
    if not isinstance(raw, dict):
        msg = "Reponse Open-Meteo inattendue (objet JSON attendu)."
        raise TypeError(msg)
    return parse_open_meteo(
        raw,
        latitude=lat,
        longitude=lon,
        resolved_address=resolved,
        timezone_name=str(raw.get("timezone") or tz),
    )
