"""Configuration des médias et URLs RSS / HTML / Google News."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from urllib.parse import quote_plus, urlencode

from helpers.common.urls import (
    GOOGLE_NEWS_RSS_BASE,
    JOURNAL_DE_MONTREAL_BASE,
    JOURNAL_DE_QUEBEC_BASE,
    LA_PRESSE_BASE,
    LE_DEVOIR_BASE,
    RADIO_CANADA_BASE,
)

Region = Literal["montreal", "quebec", "all"]
FetchMethod = Literal["rss", "google_news", "html"]

OUTLET_IDS = (
    "la_presse",
    "le_devoir",
    "journal_de_montreal",
    "journal_de_quebec",
    "radio_canada",
)


@dataclass(frozen=True, slots=True)
class OutletConfig:
    """Un média + feeds par région."""

    id: str
    label: str
    portal_url: str
    regions: tuple[Region, ...]
    rss_by_region: dict[str, tuple[str, ...]]
    html_by_region: dict[str, tuple[str, ...]]
    google_query_by_region: dict[str, str]
    site_host: str


def google_news_rss_url(query: str) -> str:
    """URL Google News RSS (hl=fr-CA) pour une requête ``site:…``."""
    params = urlencode(
        {
            "q": query,
            "hl": "fr-CA",
            "gl": "CA",
            "ceid": "CA:fr",
        },
        quote_via=quote_plus,
    )
    return f"{GOOGLE_NEWS_RSS_BASE}?{params}"


OUTLETS: dict[str, OutletConfig] = {
    "la_presse": OutletConfig(
        id="la_presse",
        label="La Presse",
        portal_url=LA_PRESSE_BASE,
        regions=("montreal", "quebec", "all"),
        rss_by_region={
            "montreal": (f"{LA_PRESSE_BASE}/actualites/grand-montreal/rss",),
            "quebec": (f"{LA_PRESSE_BASE}/actualites/regional/rss",),
            "all": (
                f"{LA_PRESSE_BASE}/actualites/grand-montreal/rss",
                f"{LA_PRESSE_BASE}/actualites/regional/rss",
                f"{LA_PRESSE_BASE}/manchettes/rss",
            ),
        },
        html_by_region={
            "montreal": (f"{LA_PRESSE_BASE}/actualites/grand-montreal/",),
            "quebec": (f"{LA_PRESSE_BASE}/actualites/regional/",),
            "all": (
                f"{LA_PRESSE_BASE}/actualites/grand-montreal/",
                f"{LA_PRESSE_BASE}/actualites/regional/",
            ),
        },
        google_query_by_region={
            "montreal": "site:lapresse.ca Montréal OR Montreal",
            "quebec": "site:lapresse.ca Québec OR Quebec",
            "all": "site:lapresse.ca",
        },
        site_host="lapresse.ca",
    ),
    "le_devoir": OutletConfig(
        id="le_devoir",
        label="Le Devoir",
        portal_url=LE_DEVOIR_BASE,
        regions=("montreal", "quebec", "all"),
        rss_by_region={
            "montreal": (f"{LE_DEVOIR_BASE}/rss/manchettes.xml",),
            "quebec": (f"{LE_DEVOIR_BASE}/rss/manchettes.xml",),
            "all": (f"{LE_DEVOIR_BASE}/rss/manchettes.xml",),
        },
        html_by_region={
            "montreal": (f"{LE_DEVOIR_BASE}/",),
            "quebec": (f"{LE_DEVOIR_BASE}/",),
            "all": (f"{LE_DEVOIR_BASE}/",),
        },
        google_query_by_region={
            "montreal": "site:ledevoir.com Montréal OR Montreal",
            "quebec": "site:ledevoir.com Québec OR Quebec",
            "all": "site:ledevoir.com",
        },
        site_host="ledevoir.com",
    ),
    "journal_de_montreal": OutletConfig(
        id="journal_de_montreal",
        label="Le Journal de Montréal",
        portal_url=JOURNAL_DE_MONTREAL_BASE,
        regions=("montreal", "all"),
        rss_by_region={
            "montreal": (f"{JOURNAL_DE_MONTREAL_BASE}/actualite/rss.xml",),
            "all": (
                f"{JOURNAL_DE_MONTREAL_BASE}/rss.xml",
                f"{JOURNAL_DE_MONTREAL_BASE}/actualite/rss.xml",
            ),
        },
        html_by_region={
            "montreal": (f"{JOURNAL_DE_MONTREAL_BASE}/",),
            "all": (f"{JOURNAL_DE_MONTREAL_BASE}/",),
        },
        google_query_by_region={
            "montreal": "site:journaldemontreal.com",
            "all": "site:journaldemontreal.com",
        },
        site_host="journaldemontreal.com",
    ),
    "journal_de_quebec": OutletConfig(
        id="journal_de_quebec",
        label="Le Journal de Québec",
        portal_url=JOURNAL_DE_QUEBEC_BASE,
        regions=("quebec", "all"),
        rss_by_region={
            "quebec": (f"{JOURNAL_DE_QUEBEC_BASE}/actualite/rss.xml",),
            "all": (
                f"{JOURNAL_DE_QUEBEC_BASE}/rss.xml",
                f"{JOURNAL_DE_QUEBEC_BASE}/actualite/rss.xml",
            ),
        },
        html_by_region={
            "quebec": (f"{JOURNAL_DE_QUEBEC_BASE}/",),
            "all": (f"{JOURNAL_DE_QUEBEC_BASE}/",),
        },
        google_query_by_region={
            "quebec": "site:journaldequebec.com",
            "all": "site:journaldequebec.com",
        },
        site_host="journaldequebec.com",
    ),
    "radio_canada": OutletConfig(
        id="radio_canada",
        label="Radio-Canada",
        portal_url=RADIO_CANADA_BASE,
        regions=("montreal", "quebec", "all"),
        rss_by_region={
            "montreal": (f"{RADIO_CANADA_BASE}/info/rss/grandmontreal/en-continu",),
            "quebec": (f"{RADIO_CANADA_BASE}/info/rss/quebec/en-continu",),
            "all": (
                f"{RADIO_CANADA_BASE}/info/rss/grandmontreal/en-continu",
                f"{RADIO_CANADA_BASE}/info/rss/quebec/en-continu",
                f"{RADIO_CANADA_BASE}/info/rss/info/a-la-une",
            ),
        },
        html_by_region={
            "montreal": (f"{RADIO_CANADA_BASE}/grandmontreal/en-continu",),
            "quebec": (f"{RADIO_CANADA_BASE}/quebec/en-continu",),
            "all": (
                f"{RADIO_CANADA_BASE}/grandmontreal/en-continu",
                f"{RADIO_CANADA_BASE}/quebec/en-continu",
            ),
        },
        google_query_by_region={
            "montreal": "site:ici.radio-canada.ca Montréal OR Montreal",
            "quebec": "site:ici.radio-canada.ca Québec OR Quebec",
            "all": "site:ici.radio-canada.ca",
        },
        site_host="ici.radio-canada.ca",
    ),
}


def resolve_rss_urls(outlet: OutletConfig, region: Region) -> tuple[str, ...]:
    if region in outlet.rss_by_region:
        return outlet.rss_by_region[region]
    return outlet.rss_by_region.get("all", ())


def resolve_html_urls(outlet: OutletConfig, region: Region) -> tuple[str, ...]:
    if region in outlet.html_by_region:
        return outlet.html_by_region[region]
    return outlet.html_by_region.get("all", ())


def resolve_google_query(outlet: OutletConfig, region: Region) -> str:
    if region in outlet.google_query_by_region:
        return outlet.google_query_by_region[region]
    return outlet.google_query_by_region.get("all", f"site:{outlet.site_host}")
