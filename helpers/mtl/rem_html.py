"""Parsers HTML rem.info (etat du reseau + actualites)."""

from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from helpers.common.config import REM_PORTAL_URL
from helpers.common.http_client import fetch_text
from helpers.mtl.rem_api import (
    _MAX_NEWS,
    _normalize_lang,
    list_news_from_rss,
    news_url_for_lang,
    status_url_for_lang,
)

_LIRE_PREFIX = re.compile(r"^(?:Lire|Read)\s+", re.IGNORECASE)


def _text(el: Tag | None) -> str:
    if el is None:
        return ""
    return " ".join(el.get_text(" ", strip=True).split())


def _abs_url(href: str | None) -> str | None:
    if not href:
        return None
    value = href.strip()
    if not value or value.startswith("#"):
        return None
    return urljoin(REM_PORTAL_URL + "/", value)


def _tab_panel(soup: BeautifulSoup, tab_id: str) -> Tag | None:
    panel = soup.find(id=tab_id)
    return panel if isinstance(panel, Tag) else None


def _tab_summary(soup: BeautifulSoup, tab_id: str) -> dict[str, Any]:
    """Read tab header link for aria-label / count."""
    link = soup.select_one(f'a[data-tab="{tab_id}"], a[href="#{tab_id}"]')
    title = None
    aria = None
    count = None
    if isinstance(link, Tag):
        title_el = link.select_one(".live-network-status__tab-title")
        title = _text(title_el) or _text(link)
        span = link.find("span", attrs={"aria-label": True})
        if isinstance(span, Tag):
            aria = span.get("aria-label")
        count_el = link.select_one(".live-network-status__tab-count")
        if isinstance(count_el, Tag):
            raw = _text(count_el)
            if raw.isdigit():
                count = int(raw)
            aria_count = count_el.get("aria-label")
            if aria_count and not aria:
                aria = aria_count
    return {"title": title or None, "label": aria or None, "count": count}


def _parse_alert_blocks(panel: Tag | None) -> list[dict[str, Any]]:
    if panel is None:
        return []
    items: list[dict[str, Any]] = []
    for block in panel.select(".live-network-status__alert-content"):
        stations_el = block.select_one(".live-network-status__trip-stations")
        stations = _text(stations_el) if stations_el else None
        date_el = block.select_one(".live-network-status__trip-details-expected-date")
        date_text = _text(date_el) if date_el else None
        details_el = block.select_one(".live-network-status__trip-details-text")
        details = _text(details_el) if details_el else None
        alt_el = block.select_one(".live-network-status__trip-details-succession-plan")
        alternatives = _text(alt_el) if alt_el else None
        alt_links: list[dict[str, str]] = []
        for a in block.select("a[href]"):
            raw_href = a.get("href")
            href = _abs_url(raw_href if isinstance(raw_href, str) else None)
            label = _text(a)
            if href and label:
                alt_links.append({"label": label, "url": href})
        if not any([stations, date_text, details, alternatives, alt_links]):
            continue
        items.append(
            {
                "stations": stations,
                "date": date_text,
                "details": details,
                "alternatives": alternatives,
                "links": alt_links or None,
            }
        )
    return items


def _parse_plain_panel(panel: Tag | None) -> dict[str, Any]:
    """Network / elevator panels are often thin (map + empty divs)."""
    if panel is None:
        return {"summary": None, "items": [], "raw_text": None}
    # Prefer explicit alert blocks if present
    items = _parse_alert_blocks(panel)
    texts: list[str] = []
    for el in panel.select(
        ".live-network-status__header-title, "
        ".live-network-status__description, "
        ".live-network-status__trip-stations h4, "
        "[aria-label]"
    ):
        if not isinstance(el, Tag):
            continue
        if el.name and el.has_attr("aria-label"):
            label = el.get("aria-label")
            if isinstance(label, str) and label.strip():
                texts.append(label.strip())
                continue
        t = _text(el)
        if t and t not in texts:
            texts.append(t)
    raw = " | ".join(texts[:12]) if texts else None
    summary = texts[0] if texts else None
    return {"summary": summary, "items": items, "raw_text": raw}


def parse_network_status_html(html: str) -> dict[str, Any]:
    """Parse rem.info network-status page into network / elevators / interruptions."""
    warnings: list[str] = []
    if not html or not html.strip():
        return {
            "network": {"summary": None, "items": []},
            "elevators": {"summary": None, "items": []},
            "interruptions": [],
            "interruption_count": 0,
            "warnings": ["HTML vide ou indisponible"],
        }
    soup = BeautifulSoup(html, "html.parser")
    service_tab = _tab_summary(soup, "tab-service")
    elevator_tab = _tab_summary(soup, "tab-elevator")
    interruption_tab = _tab_summary(soup, "tab-interruption")

    service_panel = _tab_panel(soup, "tab-service")
    elevator_panel = _tab_panel(soup, "tab-elevator")
    interruption_panel = _tab_panel(soup, "tab-interruption")

    if service_panel is None:
        warnings.append("Panneau tab-service introuvable (layout rem.info change?)")
    if elevator_panel is None:
        warnings.append("Panneau tab-elevator introuvable (layout rem.info change?)")
    if interruption_panel is None:
        warnings.append("Panneau tab-interruption introuvable (layout rem.info change?)")

    network = _parse_plain_panel(service_panel)
    if service_tab.get("label") and not network.get("summary"):
        network["summary"] = service_tab["label"]
    network["tab"] = service_tab

    elevators = _parse_plain_panel(elevator_panel)
    if elevator_tab.get("label") and not elevators.get("summary"):
        elevators["summary"] = elevator_tab["label"]
    elevators["tab"] = elevator_tab

    interruptions = _parse_alert_blocks(interruption_panel)
    count = interruption_tab.get("count")
    if count is None:
        count = len(interruptions)

    return {
        "network": network,
        "elevators": elevators,
        "interruptions": interruptions,
        "interruption_count": count,
        "warnings": warnings,
    }


def parse_news_html(html: str, *, limit: int = 15) -> list[dict[str, Any]]:
    """Parse rem.info news listing tiles."""
    lim = max(1, min(int(limit), _MAX_NEWS))
    if not html or not html.strip():
        return []
    soup = BeautifulSoup(html, "html.parser")
    articles = soup.select("article.thumb")
    if not articles:
        articles = soup.select(".common-tile article, .filtered-tiles article")
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for article in articles:
        if not isinstance(article, Tag):
            continue
        link = article.select_one("a[href]")
        if not isinstance(link, Tag):
            continue
        raw_href = link.get("href")
        href = _abs_url(raw_href if isinstance(raw_href, str) else None)
        if not href or href in seen:
            continue
        title_el = article.select_one("h3")
        title = _text(title_el)
        if not title:
            aria = link.get("aria-label") or link.get("title")
            if isinstance(aria, str):
                title = _LIRE_PREFIX.sub("", aria).strip()
        if not title:
            continue
        category = _text(article.select_one(".thumb--tag")) or None
        published = _text(article.select_one(".thumb--date")) or None
        seen.add(href)
        items.append(
            {
                "title": title,
                "url": href,
                "category": category,
                "published_at": published,
                "summary": None,
            }
        )
        if len(items) >= lim:
            break
    return items


async def get_network_status(*, lang: str = "fr") -> dict[str, Any]:
    """Fetch + parse REM network status page."""
    normalized = _normalize_lang(lang)
    page_lang = "en" if normalized == "en" else "fr"
    url = status_url_for_lang(page_lang)
    warnings: list[str] = []
    try:
        html = await fetch_text(url, use_cache=True)
    except Exception as exc:
        return {
            "lang": page_lang,
            "network": {"summary": None, "items": []},
            "elevators": {"summary": None, "items": []},
            "interruptions": [],
            "interruption_count": 0,
            "source_url": url,
            "fetched_at": int(time.time()),
            "warnings": [f"Impossible de telecharger l'etat du reseau: {exc}"],
        }
    parsed = parse_network_status_html(html)
    warnings.extend(parsed.pop("warnings", []) or [])
    return {
        "lang": page_lang,
        **parsed,
        "source_url": url,
        "fetched_at": int(time.time()),
        "warnings": warnings,
    }


async def list_news(*, lang: str = "fr", limit: int = 15) -> dict[str, Any]:
    """Actualites REM: RSS d'abord, HTML si le flux est vide."""
    normalized = _normalize_lang(lang)
    page_lang = "en" if normalized == "en" else "fr"
    lim = max(1, min(int(limit), _MAX_NEWS))
    warnings: list[str] = []

    try:
        rss_payload = await list_news_from_rss(lang=page_lang, limit=lim)
    except Exception as exc:
        rss_payload = {
            "items": [],
            "rss_url": None,
            "news_url": news_url_for_lang(page_lang),
        }
        warnings.append(f"RSS indisponible: {exc}")

    items = list(rss_payload.get("items") or [])
    fetch_method = "rss"
    if not items:
        news_url = news_url_for_lang(page_lang)
        try:
            html = await fetch_text(news_url, use_cache=True)
            items = parse_news_html(html, limit=lim)
            fetch_method = "html"
            if not items:
                warnings.append("Aucune actualite trouvee (RSS vide + HTML sans tuiles)")
        except Exception as exc:
            warnings.append(f"HTML actualites indisponible: {exc}")
            fetch_method = "none"

    return {
        "lang": page_lang,
        "total": len(items),
        "items": items,
        "fetch_method": fetch_method,
        "rss_url": rss_payload.get("rss_url"),
        "news_url": news_url_for_lang(page_lang),
        "fetched_at": int(time.time()),
        "warnings": warnings,
    }
