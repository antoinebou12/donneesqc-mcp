"""Client pour la Vitrine linguistique (OQLF) - recherche HTML Solr."""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from helpers.common.config import VITRINE_BASE_URL
from helpers.common.http_client import fetch_text
from helpers.common.urls import VITRINE_BASE

SEARCH_PATH = "/resultats-de-recherche"
SOURCE = VITRINE_BASE


def _absolute_url(href: str) -> str:
    return urljoin(VITRINE_BASE_URL + "/", href)


def _detect_type(text: str, href: str) -> str:
    blob = f"{text} {href}".lower()
    if "gdt" in blob or "dictionnaire" in blob or "terminolog" in blob:
        return "gdt"
    if "bdl" in blob or "depannage" in blob or "dépannage" in blob:
        return "bdl"
    return "unknown"


def parse_search_results(html: str, *, limit: int = 10) -> list[dict[str, Any]]:
    """Extrait les resultats de recherche depuis le HTML de la Vitrine."""
    soup = BeautifulSoup(html, "html.parser")
    results: list[dict[str, Any]] = []

    # Resultats typiques : titres h2/h3 avec liens, ou listes de resultats Solr
    candidates = soup.select("h2 a, h3 a, .tx-solr-result a, article a, .result a")
    seen: set[str] = set()

    for link in candidates:
        title = " ".join(link.get_text(strip=True).split())
        raw_href = link.get("href")
        href = raw_href if isinstance(raw_href, str) else ""
        if not title or not href or href.startswith("#"):
            continue
        url = _absolute_url(href)
        if url in seen:
            continue
        # Ignorer navigation / filtres
        if any(skip in url for skip in ("#", "javascript:", "/nous-joindre")):
            continue
        if "/resultats-de-recherche" in url and "tx_solr" not in url:
            continue

        # Bloc resultat : parent article/li, sinon h2/h3 + freres suivants
        heading = link.find_parent(["h2", "h3"])
        parent = link.find_parent(["article", "li"]) or heading
        snippet = ""
        content_type = "unknown"
        texts: list[str] = []
        if parent:
            texts.append(parent.get_text(" ", strip=True))
            texts.extend(
                sib.get_text(" ", strip=True) for sib in parent.find_next_siblings(["div", "p", "span", "section"])[:4]
            )
        blob = " ".join(texts)
        lower = blob.lower()
        if "contenu bdl" in lower or " contenu bdl" in f" {lower}":
            content_type = "bdl"
        elif "contenu gdt" in lower:
            content_type = "gdt"
        else:
            content_type = _detect_type(blob + " " + title, href)
        for text in texts:
            cleaned = " ".join(text.split())
            if len(cleaned) > 40 and cleaned != title and not snippet:
                snippet = cleaned[:400]

        seen.add(url)
        results.append(
            {
                "title": title,
                "url": url,
                "type": content_type,
                "snippet": snippet,
            }
        )
        if len(results) >= limit:
            break

    return results


def parse_entry(html: str, url: str) -> dict[str, Any]:
    """Extrait titre et extrait principal d'une fiche Vitrine."""
    soup = BeautifulSoup(html, "html.parser")
    title_el = soup.find("h1")
    title = title_el.get_text(strip=True) if title_el else ""

    main = soup.find("main") or soup.find("article") or soup.body
    excerpt = ""
    if main:
        paragraphs = main.find_all("p")
        chunks: list[str] = []
        for p in paragraphs:
            text = " ".join(p.get_text(" ", strip=True).split())
            if len(text) > 20:
                chunks.append(text)
            if sum(len(c) for c in chunks) > 800:
                break
        excerpt = " ".join(chunks)[:1000]

    return {
        "title": title,
        "url": url,
        "excerpt": excerpt,
        "source": SOURCE,
    }


async def search_vitrine(
    query: str,
    *,
    include_bdl: bool = True,
    include_gdt: bool = True,
    limit: int = 10,
) -> dict[str, Any]:
    """Recherche dans la Vitrine linguistique (BDL et/ou GDT)."""
    params: dict[str, Any] = {"tx_solr[q]": query}
    filters: list[str] = []
    if include_bdl:
        filters.append("type_stringM:bdl")
    if include_gdt:
        filters.append("type_stringM:gdt")
    for i, f in enumerate(filters):
        params[f"tx_solr[filter][{i}]"] = f

    url = f"{VITRINE_BASE_URL}{SEARCH_PATH}"
    html = await fetch_text(url, params=params)
    results = parse_search_results(html, limit=limit)
    return {
        "query": query,
        "total_returned": len(results),
        "results": results,
        "source": SOURCE,
        "search_url": url,
    }


async def get_vitrine_entry(url: str) -> dict[str, Any]:
    """Recupere le contenu resume d'une fiche Vitrine."""
    if not url.startswith("http"):
        url = _absolute_url(url)
    if not url.startswith(VITRINE_BASE_URL):
        msg = "URL hors domaine Vitrine linguistique"
        raise ValueError(msg)
    html = await fetch_text(url)
    return parse_entry(html, url)
