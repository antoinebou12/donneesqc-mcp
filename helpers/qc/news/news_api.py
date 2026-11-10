"""Agrégation async des manchettes (RSS → Google News → HTML)."""

from __future__ import annotations

import asyncio
import logging
import re
import unicodedata
from datetime import UTC, date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from helpers.common.http_client import fetch_text
from helpers.common.urls import LA_PRESSE_BASE
from helpers.mtl.events_common import clamp_limit
from helpers.qc.news.feeds import (
    OUTLET_IDS,
    OUTLETS,
    OutletConfig,
    Region,
    google_news_rss_url,
    resolve_google_query,
    resolve_html_urls,
    resolve_rss_urls,
)
from helpers.qc.news.html_parse import parse_html_headlines
from helpers.qc.news.rss_parse import parse_rss_items

logger = logging.getLogger(__name__)

_TZ = ZoneInfo("America/Toronto")
_VALID_REGIONS = frozenset({"montreal", "quebec", "all"})

_MONTREAL_HINTS = (
    "montreal",
    "montréal",
    "laval",
    "longueuil",
    "brossard",
    "terrebonne",
    "repentigny",
    "boucherville",
    "saint-lambert",
    "saint-hubert",
    "dorval",
    "pointe-claire",
    "westmount",
    "outremont",
    "verdun",
    "plateau",
    "vieux-montreal",
    "rive-nord",
    "rive-sud",
)
_QUEBEC_HINTS = (
    "quebec",
    "québec",
    "levis",
    "lévis",
    "sainte-foy",
    "beauport",
    "charlesbourg",
    "capitale-nationale",
)


def _fold(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def resolve_region_from_address(address: str) -> Region | None:
    """Heuristique ville → region (pas de géocode v1)."""
    folded = _fold(address)
    has_mtl = any(h in folded for h in _MONTREAL_HINTS)
    if has_mtl:
        return "montreal"
    if re.search(
        r"\b(ville de quebec|quebec city|levis|beauport|sainte-foy|"
        r"charlesbourg|capitale-nationale)\b",
        folded,
    ):
        return "quebec"
    # "…, Québec" / "…, QC" without Montréal cues → Québec city bias for JdeQ
    if re.search(r",\s*(quebec|qc)\b", folded) and any(h in folded for h in _QUEBEC_HINTS):
        return "quebec"
    return None


def _today_toronto(now: datetime | None = None) -> date:
    current = now or datetime.now(_TZ)
    if current.tzinfo is None:
        current = current.replace(tzinfo=_TZ)
    return current.astimezone(_TZ).date()


def _item_date_toronto(published_at: str | None) -> date | None:
    if not published_at:
        return None
    try:
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(_TZ).date()
    except ValueError:
        return None


def _dedupe_key(item: dict[str, Any]) -> str:
    return (item.get("url") or item.get("title") or "").strip().lower()


async def _fetch_items_from_urls(
    urls: tuple[str, ...],
    *,
    parser: str,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for url in urls:
        try:
            text = await fetch_text(url)
        except Exception:
            logger.debug("fetch failed %s", url, exc_info=True)
            continue
        parsed = parse_rss_items(text) if parser == "rss" else parse_html_headlines(text, base_url=url)
        items.extend(parsed)
    return items


async def fetch_outlet(
    outlet: OutletConfig,
    *,
    region: Region,
) -> tuple[list[dict[str, Any]], list[str], str | None]:
    """Chaîne RSS → Google News → HTML. Retourne items, warnings, fetch_method."""
    warnings: list[str] = []
    label = outlet.label

    rss_urls = resolve_rss_urls(outlet, region)
    if rss_urls:
        items = await _fetch_items_from_urls(rss_urls, parser="rss")
        if items:
            return items, warnings, "rss"
        warnings.append(f"{label}: fil RSS vide ou indisponible.")

    gquery = resolve_google_query(outlet, region)
    gurl = google_news_rss_url(gquery)
    try:
        gtext = await fetch_text(gurl)
        gitems = parse_rss_items(gtext)
        if gitems:
            return gitems, warnings, "google_news"
        warnings.append(f"{label}: Google News RSS sans résultat.")
    except Exception:
        logger.debug("google news failed for %s", outlet.id, exc_info=True)
        warnings.append(f"{label}: Google News RSS inaccessible.")

    html_urls = resolve_html_urls(outlet, region)
    if html_urls:
        items = await _fetch_items_from_urls(html_urls, parser="html")
        if items:
            return items, warnings, "html"
        warnings.append(f"{label}: scrape HTML sans titre extractible.")

    warnings.append(f"{label}: aucune manchettes récupérée.")
    return [], warnings, None


def _normalize_sources(sources: list[str] | None) -> list[str]:
    if not sources:
        return list(OUTLET_IDS)
    cleaned: list[str] = []
    for raw in sources:
        key = (raw or "").strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "lapresse": "la_presse",
            "presse": "la_presse",
            "devoir": "le_devoir",
            "jdm": "journal_de_montreal",
            "journaldemontreal": "journal_de_montreal",
            "jdq": "journal_de_quebec",
            "journaldequebec": "journal_de_quebec",
            "radio-canada": "radio_canada",
            "radiocanada": "radio_canada",
            "cbc": "radio_canada",
        }
        key = aliases.get(key, key)
        if key not in OUTLETS:
            raise ValueError(f"Source inconnue '{raw}'. Utilisez: {', '.join(OUTLET_IDS)}.")
        if key not in cleaned:
            cleaned.append(key)
    return cleaned


def _enrich(
    raw: dict[str, Any],
    *,
    outlet: OutletConfig,
    region: Region,
    fetch_method: str,
) -> dict[str, Any]:
    return {
        "title": raw["title"],
        "url": raw["url"],
        "source": outlet.id,
        "source_label": outlet.label,
        "published_at": raw.get("published_at"),
        "region": region if region != "all" else _guess_item_region(outlet),
        "summary": raw.get("summary"),
        "fetch_method": fetch_method,
    }


def _guess_item_region(outlet: OutletConfig) -> str:
    if outlet.id == "journal_de_quebec":
        return "quebec"
    if outlet.id == "journal_de_montreal":
        return "montreal"
    return "all"


async def aggregate_headlines(
    *,
    region: str = "montreal",
    today: bool = True,
    sources: list[str] | None = None,
    query: str | None = None,
    address: str | None = None,
    limit: int = 20,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Fusionne les médias, filtre, trie par date décroissante."""
    region_key = (region or "montreal").strip().lower()
    if region_key not in _VALID_REGIONS:
        raise ValueError("region doit être montreal, quebec ou all.")

    if address and address.strip():
        resolved = resolve_region_from_address(address.strip())
        if resolved:
            region_key = resolved

    outlet_ids = _normalize_sources(sources)
    # Skip outlets that don't cover the requested region
    selected: list[OutletConfig] = []
    for oid in outlet_ids:
        outlet = OUTLETS[oid]
        if region_key == "all" or region_key in outlet.regions:
            selected.append(outlet)

    limit = clamp_limit(limit, max_limit=50)
    typed_region: Region = region_key  # type: ignore[assignment]

    results = await asyncio.gather(
        *[fetch_outlet(o, region=typed_region) for o in selected],
        return_exceptions=True,
    )

    headlines: list[dict[str, Any]] = []
    warnings: list[str] = []
    methods: dict[str, str] = {}

    for outlet, result in zip(selected, results, strict=True):
        if isinstance(result, BaseException):
            logger.warning("outlet %s failed: %s", outlet.id, result)
            warnings.append(f"{outlet.label}: erreur ({result!s}).")
            continue
        items, outlet_warnings, method = result
        warnings.extend(outlet_warnings)
        if method:
            methods[outlet.id] = method
        headlines.extend(
            _enrich(
                raw,
                outlet=outlet,
                region=typed_region,
                fetch_method=method or "rss",
            )
            for raw in items
        )

    # Dedupe by URL
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in headlines:
        key = _dedupe_key(item)
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    if today:
        today_d = _today_toronto(now)
        kept: list[dict[str, Any]] = []
        undated_count = 0
        for h in deduped:
            d = _item_date_toronto(h.get("published_at"))
            if d is None:
                kept.append(h)
                undated_count += 1
            elif d == today_d:
                kept.append(h)
        if undated_count and any(h.get("published_at") for h in kept):
            warnings.append("Filtre « today » : items sans date publiée inclus (HTML/fallback).")
        if not kept and deduped:
            warnings.append("Aucune manchette datée d'aujourd'hui (America/Toronto) ; élargissez avec today=false.")
        deduped = kept

    if query and query.strip():
        q = query.strip().lower()
        deduped = [h for h in deduped if q in (h.get("title") or "").lower() or q in (h.get("summary") or "").lower()]

    # Dated first (newest), then undated
    deduped.sort(
        key=lambda h: (
            1 if h.get("published_at") else 0,
            h.get("published_at") or "",
        ),
        reverse=True,
    )

    capped = deduped[:limit]
    portal_urls = {o.id: o.portal_url for o in selected}

    warning_text = " | ".join(dict.fromkeys(warnings)) if warnings else None

    return {
        "query": {
            "region": region_key,
            "today": today,
            "sources": [o.id for o in selected],
            "query": (query or "").strip() or None,
            "address": (address or "").strip() or None,
            "limit": limit,
        },
        "count": len(capped),
        "headlines": capped,
        "fetch_methods": methods,
        "warnings": warnings,
        "warning": warning_text,
        "sources": portal_urls,
        "portal_url": LA_PRESSE_BASE,
    }
