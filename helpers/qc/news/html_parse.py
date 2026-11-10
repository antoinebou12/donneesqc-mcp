"""Extracteurs HTML minimalistes pour pages section (fallback)."""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

_MIN_TITLE_LEN = 12
_MAX_ITEMS = 40


def _normalize(text: str) -> str:
    return " ".join(text.split()).strip()


def _same_host(base: str, href: str) -> bool:
    try:
        base_host = urlparse(base).netloc.lower().removeprefix("www.")
        href_host = urlparse(href).netloc.lower().removeprefix("www.")
        return bool(href_host) and (href_host == base_host or href_host.endswith("." + base_host))
    except ValueError:
        return False


def _looks_like_article(href: str, title: str) -> bool:
    path = urlparse(href).path.lower()
    if len(title) < _MIN_TITLE_LEN:
        return False
    if path in {"", "/", "/rss", "/rss.xml"}:
        return False
    skip_bits = (
        "/rss",
        "/login",
        "/compte",
        "/infolettre",
        "/publicite",
        "/tag/",
        "/auteur/",
        "#",
    )
    if any(b in href.lower() for b in skip_bits):
        return False
    # Prefer paths that look like articles (digit id or long slug)
    if any(ch.isdigit() for ch in path):
        return True
    return path.count("/") >= 2 and len(path) > 20


def parse_html_headlines(html: str, *, base_url: str) -> list[dict[str, Any]]:
    """Collecte des liens titre→URL depuis une page section.

    Tolère les changements de layout : retourne [] si rien d'extractible.
    """
    if not html or not html.strip():
        return []
    soup = BeautifulSoup(html, "html.parser")
    results: list[dict[str, Any]] = []
    seen: set[str] = set()

    candidates = soup.select(
        "article a[href], h2 a[href], h3 a[href], "
        ".story a[href], .card a[href], .headline a[href], "
        "a.story-card__link[href], a[data-testid='card-headline']"
    )
    if not candidates:
        candidates = soup.select("a[href]")

    for anchor in candidates:
        href_raw = anchor.get("href")
        if not isinstance(href_raw, str) or not href_raw.strip():
            continue
        href = urljoin(base_url, href_raw.strip())
        if not href.startswith("http"):
            continue
        if not _same_host(base_url, href):
            continue
        title = _normalize(anchor.get_text(" ", strip=True))
        if not title:
            title_attr = anchor.get("title")
            if isinstance(title_attr, str):
                title = _normalize(title_attr)
        if not _looks_like_article(href, title):
            continue
        if href in seen:
            continue
        seen.add(href)
        results.append(
            {
                "title": title,
                "url": href,
                "published_at": None,
                "summary": None,
            }
        )
        if len(results) >= _MAX_ITEMS:
            break
    return results
