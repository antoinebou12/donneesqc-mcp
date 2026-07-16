"""Contexte utilisateur : date/heure, GPS agent, IP client (jamais l'hôte MCP)."""

from __future__ import annotations

import ipaddress
import logging
from datetime import date as date_type
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from helpers.common.config import DEFAULT_TIMEZONE, IP_GEO_URL_TEMPLATE
from helpers.common.http_client import fetch_json

logger = logging.getLogger(__name__)

DEFAULT_TZ_NAME = DEFAULT_TIMEZONE


def resolve_timezone(name: str | None = None) -> ZoneInfo | timezone:
    """Return ZoneInfo for ``name`` or DEFAULT_TIMEZONE; UTC-4 fallback without tzdata."""
    raw = (name or "").strip() or DEFAULT_TZ_NAME
    try:
        return ZoneInfo(raw)
    except ZoneInfoNotFoundError:
        if raw == DEFAULT_TZ_NAME or not name:
            return timezone(timedelta(hours=-4))
        msg = f"Fuseau horaire inconnu: {raw}"
        raise ValueError(msg) from None


def resolve_now(
    *,
    date: str | None = None,
    timezone_name: str | None = None,
) -> dict[str, Any]:
    """Resolve « now » from agent date/timezone or America/Toronto.

    Returns keys: date, datetime_iso, timezone, time_source (agent|default).
    """
    tz = resolve_timezone(timezone_name)
    now = datetime.now(tz)
    cleaned = (date or "").strip()
    if cleaned:
        try:
            day = date_type.fromisoformat(cleaned[:10])
        except ValueError as exc:
            msg = "Date invalide (utilisez YYYY-MM-DD)."
            raise ValueError(msg) from exc
        combined = datetime(
            day.year,
            day.month,
            day.day,
            now.hour,
            now.minute,
            now.second,
            tzinfo=tz,
        )
        return {
            "date": day.isoformat(),
            "datetime_iso": combined.isoformat(),
            "timezone": str(getattr(tz, "key", None) or timezone_name or DEFAULT_TZ_NAME),
            "time_source": "agent",
        }
    return {
        "date": now.date().isoformat(),
        "datetime_iso": now.isoformat(),
        "timezone": str(getattr(tz, "key", None) or DEFAULT_TZ_NAME),
        "time_source": "default",
    }


def is_public_ip(ip: str) -> bool:
    """True if ``ip`` is globally routable (excludes private, loopback, doc ranges)."""
    try:
        addr = ipaddress.ip_address(ip.strip())
    except ValueError:
        return False
    return bool(addr.is_global)


def _headers_from_request(request: Any) -> dict[str, str]:
    headers = getattr(request, "headers", None)
    if headers is None:
        return {}
    try:
        return {str(k).lower(): str(v) for k, v in headers.items()}
    except Exception:
        return {}


def client_ip_from_headers(headers: dict[str, str]) -> str | None:
    """Extract client IP from X-Forwarded-For / X-Real-IP (first public hop)."""
    forwarded = headers.get("x-forwarded-for") or headers.get("x-forwarded_for")
    if forwarded:
        for part in forwarded.split(","):
            candidate = part.strip().strip("[]")
            if candidate.count(":") == 1 and "." in candidate:
                candidate = candidate.rsplit(":", 1)[0]
            if is_public_ip(candidate):
                return candidate
    for key in ("x-real-ip", "cf-connecting-ip", "true-client-ip"):
        raw = headers.get(key)
        if raw:
            candidate = raw.strip().strip("[]")
            if is_public_ip(candidate):
                return candidate
    return None


def read_client_ip() -> str | None:
    """Read public client IP from the current MCP HTTP request, if any.

    Never returns the MCP host egress address. Returns None outside HTTP context
    or when only private/proxy-local addresses are present.
    """
    try:
        from mcp.server.lowlevel.server import request_ctx

        rc = request_ctx.get()
    except LookupError:
        return None
    except Exception:
        logger.debug("read_client_ip: request context unavailable", exc_info=True)
        return None

    request = getattr(rc, "request", None)
    if request is None:
        return None

    headers = _headers_from_request(request)
    ip = client_ip_from_headers(headers)
    if ip:
        return ip

    client = getattr(request, "client", None)
    host = getattr(client, "host", None) if client is not None else None
    if isinstance(host, str) and is_public_ip(host):
        return host
    return None


async def geolocate_client_ip(ip: str) -> dict[str, Any]:
    """Geolocate a **client** IP via configured no-key API. Never looks up « self »."""
    cleaned = (ip or "").strip()
    if not cleaned:
        msg = "Adresse IP client manquante (ne jamais geolocaliser l'hote MCP)."
        raise ValueError(msg)
    if not is_public_ip(cleaned):
        msg = "Adresse IP non publique (privee/loopback) - geolocalisation refusee."
        raise ValueError(msg)

    url = IP_GEO_URL_TEMPLATE.format(ip=cleaned)
    data = await fetch_json(url, use_cache=True)
    if not isinstance(data, dict):
        msg = "Reponse geolocalisation IP inattendue."
        raise TypeError(msg)
    if data.get("error") or data.get("reason"):
        msg = f"Geolocalisation IP echouee: {data.get('reason') or data.get('error')}"
        raise RuntimeError(msg)

    lat = data.get("latitude")
    lon = data.get("longitude")
    if lat is None or lon is None:
        lat = data.get("lat")
        lon = data.get("lon")
    if lat is None or lon is None:
        msg = "Coordonnees manquantes dans la reponse geolocalisation IP."
        raise ValueError(msg)
    try:
        latitude = float(lat)
        longitude = float(lon)
    except (TypeError, ValueError) as exc:
        msg = "Coordonnees manquantes dans la reponse geolocalisation IP."
        raise ValueError(msg) from exc

    city = data.get("city") or data.get("town")
    region = data.get("region") or data.get("regionName") or data.get("region_code")
    country = data.get("country_name") or data.get("country")
    label_parts = [p for p in (city, region, country) if p]
    return {
        "latitude": latitude,
        "longitude": longitude,
        "city": city,
        "region": region,
        "country": country,
        "label": ", ".join(str(p) for p in label_parts) if label_parts else None,
        "ip": cleaned,
        "location_source": "client_ip",
    }


async def resolve_user_location(
    *,
    latitude: float | None = None,
    longitude: float | None = None,
    address: str | None = None,
    allow_client_ip: bool = True,
    client_ip: str | None = None,
) -> dict[str, Any]:
    """Resolve user location: agent GPS → address → optional client IP geo.

    Never geolocates the MCP host egress IP.
    """
    from helpers.mtl.avis_api import geocode_address
    from helpers.mtl.geo import validate_wgs84

    resolved_address: str | None = address.strip() if address and address.strip() else None

    if latitude is not None and longitude is not None:
        lat = float(latitude)
        lon = float(longitude)
        validate_wgs84(lat, lon)
        return {
            "latitude": lat,
            "longitude": lon,
            "resolved_address": resolved_address,
            "location_source": "agent",
            "city": None,
            "label": resolved_address,
            "client_ip": None,
        }

    if resolved_address:
        lat, lon, geocoded = await geocode_address(resolved_address)
        return {
            "latitude": lat,
            "longitude": lon,
            "resolved_address": geocoded,
            "location_source": "address",
            "city": None,
            "label": geocoded,
            "client_ip": None,
        }

    if allow_client_ip:
        ip = (client_ip or "").strip() or read_client_ip()
        if ip:
            geo = await geolocate_client_ip(ip)
            return {
                "latitude": geo["latitude"],
                "longitude": geo["longitude"],
                "resolved_address": geo.get("label"),
                "location_source": "client_ip",
                "city": geo.get("city"),
                "label": geo.get("label"),
                "client_ip": ip,
            }

    msg = (
        "Fournissez latitude/longitude (GPS telephone/PC), une address, "
        "ou assurez une IP client publique (X-Forwarded-For). "
        "L'IP du serveur MCP n'est jamais utilisee."
    )
    raise ValueError(msg)


async def build_user_context(
    *,
    latitude: float | None = None,
    longitude: float | None = None,
    address: str | None = None,
    date: str | None = None,
    timezone_name: str | None = None,
    include_client_ip: bool = True,
    allow_client_ip_geo: bool = True,
) -> dict[str, Any]:
    """Build the common_get_context payload."""
    now = resolve_now(date=date, timezone_name=timezone_name)
    client_ip = read_client_ip() if include_client_ip else None

    location: dict[str, Any] | None = None
    location_error: str | None = None
    has_coords = latitude is not None and longitude is not None
    has_address = bool(address and address.strip())
    if has_coords or has_address or allow_client_ip_geo:
        try:
            location = await resolve_user_location(
                latitude=latitude,
                longitude=longitude,
                address=address,
                allow_client_ip=allow_client_ip_geo and not (has_coords or has_address),
                client_ip=client_ip,
            )
        except ValueError as exc:
            location_error = str(exc)
            location = None

    return {
        "now": now,
        "client_ip": client_ip if include_client_ip else None,
        "location": location,
        "location_error": location_error,
        "hints": {
            "prefer": "Pass phone GPS (latitude/longitude) and system date/timezone when available.",
            "never": "MCP host egress IP is never used for geolocation.",
        },
    }
