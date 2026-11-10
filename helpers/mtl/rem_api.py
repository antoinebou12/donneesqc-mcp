"""REM GTFS-RT alertes et flux RSS actualites."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any, Literal
from urllib.parse import urljoin

from google.transit import gtfs_realtime_pb2

from helpers.common.config import (
    REM_GTFS_RT_ALERTS_URL,
    REM_NEWS_URL_EN,
    REM_NEWS_URL_FR,
    REM_PORTAL_URL,
    REM_RSS_URL_EN,
    REM_RSS_URL_FR,
    REM_STATUS_URL_EN,
    REM_STATUS_URL_FR,
)
from helpers.common.http_client import fetch_bytes, fetch_text
from helpers.common.maps_format import attach_nearby_maps
from helpers.mtl.rem_gtfs import filter_stops_nearby, load_stops
from helpers.qc.news.rss_parse import parse_rss_items

Lang = Literal["fr", "en", "all"]

_MAX_NEWS = 50
_MAX_ALERTS = 100


def _normalize_lang(lang: str) -> Lang:
    value = (lang or "fr").strip().lower()
    if value not in {"fr", "en", "all"}:
        msg = "lang doit etre fr, en ou all."
        raise ValueError(msg)
    return value  # type: ignore[return-value]


def status_url_for_lang(lang: str) -> str:
    return REM_STATUS_URL_EN if _normalize_lang(lang) == "en" else REM_STATUS_URL_FR


def news_url_for_lang(lang: str) -> str:
    return REM_NEWS_URL_EN if _normalize_lang(lang) == "en" else REM_NEWS_URL_FR


def rss_url_for_lang(lang: str) -> str:
    return REM_RSS_URL_EN if _normalize_lang(lang) == "en" else REM_RSS_URL_FR


def _pick_translation(
    translations: Any,
    *,
    lang: Lang,
) -> tuple[str | None, str | None]:
    """Return (text, language) preferring ``lang``, else first available."""
    if not translations:
        return None, None
    by_lang: dict[str, str] = {}
    for tr in translations:
        text = (getattr(tr, "text", None) or "").strip()
        if not text:
            continue
        code = (getattr(tr, "language", None) or "").strip().lower() or "und"
        by_lang[code] = text
    if not by_lang:
        return None, None
    if lang != "all":
        for key in (lang, lang[:2], "fr", "en", "und"):
            if key in by_lang:
                return by_lang[key], key
    # Prefer French then English then any
    for key in ("fr", "en"):
        if key in by_lang:
            return by_lang[key], key
    first_key = next(iter(by_lang))
    return by_lang[first_key], first_key


def _ts_iso(ts: int) -> str | None:
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (OverflowError, OSError, ValueError):
        return None


def parse_gtfs_rt_alerts(
    feed: gtfs_realtime_pb2.FeedMessage,
    *,
    lang: Lang = "fr",
) -> list[dict[str, Any]]:
    """Normalize GTFS-RT FeedMessage alerts."""
    alerts: list[dict[str, Any]] = []
    for entity in feed.entity:
        if not entity.HasField("alert"):
            continue
        alert = entity.alert
        header, header_lang = _pick_translation(alert.header_text.translation, lang=lang)
        description, desc_lang = _pick_translation(
            alert.description_text.translation,
            lang=lang,
        )
        periods = [
            {
                "start": _ts_iso(period.start),
                "end": _ts_iso(period.end),
                "start_unix": int(period.start) if period.start else None,
                "end_unix": int(period.end) if period.end else None,
            }
            for period in alert.active_period
        ]
        informed: list[dict[str, Any]] = []
        for ie in alert.informed_entity:
            row: dict[str, Any] = {}
            if ie.agency_id:
                row["agency_id"] = ie.agency_id
            if ie.route_id:
                row["route_id"] = ie.route_id
            if ie.route_type:
                row["route_type"] = ie.route_type
            if ie.HasField("trip") and ie.trip.trip_id:
                row["trip_id"] = ie.trip.trip_id
            if ie.stop_id:
                row["stop_id"] = ie.stop_id
            if row:
                informed.append(row)
        cause = None
        effect = None
        try:
            cause = alert.Cause.Name(alert.cause) if alert.cause else None
        except ValueError:
            cause = str(alert.cause) if alert.cause else None
        try:
            effect = alert.Effect.Name(alert.effect) if alert.effect else None
        except ValueError:
            effect = str(alert.effect) if alert.effect else None
        alerts.append(
            {
                "id": entity.id or None,
                "header": header,
                "description": description,
                "language": header_lang or desc_lang,
                "cause": cause,
                "effect": effect,
                "active_period": periods,
                "informed_entities": informed,
            }
        )
        if len(alerts) >= _MAX_ALERTS:
            break
    return alerts


async def fetch_alerts_feed() -> gtfs_realtime_pb2.FeedMessage:
    raw = await fetch_bytes(
        REM_GTFS_RT_ALERTS_URL,
        headers={"Accept": "application/x-protobuf"},
    )
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(raw)
    return feed


async def list_service_alerts(*, lang: str = "fr") -> dict[str, Any]:
    """Alertes GTFS-RT REM (ouvertures tardives, interruptions, etc.)."""
    normalized = _normalize_lang(lang)
    feed = await fetch_alerts_feed()
    alerts = parse_gtfs_rt_alerts(feed, lang=normalized)
    header_ts = int(feed.header.timestamp) if feed.header.timestamp else None
    return {
        "lang": normalized,
        "total": len(alerts),
        "alerts": alerts,
        "fetched_at": int(time.time()),
        "feed_timestamp": _ts_iso(header_ts) if header_ts else None,
        "alerts_url": REM_GTFS_RT_ALERTS_URL,
        "status_url": status_url_for_lang(normalized if normalized != "all" else "fr"),
        "portal_url": REM_PORTAL_URL,
    }


async def list_news_from_rss(*, lang: str = "fr", limit: int = 15) -> dict[str, Any]:
    """Fetch REM RSS; may return empty items (feed often empty)."""
    normalized = _normalize_lang(lang)
    if normalized == "all":
        # Prefer French channel for "all"
        url = REM_RSS_URL_FR
        page_lang = "fr"
    else:
        url = rss_url_for_lang(normalized)
        page_lang = normalized
    lim = max(1, min(int(limit), _MAX_NEWS))
    text = await fetch_text(url, use_cache=True)
    items = parse_rss_items(text)[:lim]
    for item in items:
        href = item.get("url") or ""
        if href.startswith("/"):
            item["url"] = urljoin(REM_PORTAL_URL + "/", href.lstrip("/"))
    return {
        "lang": page_lang,
        "total": len(items),
        "items": items,
        "fetch_method": "rss",
        "rss_url": url,
        "news_url": news_url_for_lang(page_lang),
        "fetched_at": int(time.time()),
    }


async def list_stops_nearby(
    *,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 800.0,
    limit: int = 15,
) -> dict[str, Any]:
    """Stations / quais REM proches (index GTFS bundlé)."""
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
    from helpers.common.config import REM_GTFS_STATIC_ZIP_URL

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
        "gtfs_static_url": REM_GTFS_STATIC_ZIP_URL,
        "portal_url": REM_PORTAL_URL,
    }
