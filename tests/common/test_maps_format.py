"""Tests for Google Maps URL helpers."""

from __future__ import annotations

from helpers.common.maps_format import (
    attach_maps_pin,
    attach_nearby_maps,
    google_maps_directions_url,
    google_maps_url,
    openstreetmap_embed_url,
    openstreetmap_url,
)


def test_google_maps_url_coords():
    url = google_maps_url(latitude=45.5088, longitude=-73.5617)
    assert url is not None
    assert url.startswith("https://www.google.com/maps/search/?api=1&query=")
    assert "45.5088" in url
    assert "-73.5617" in url


def test_google_maps_url_address():
    url = google_maps_url(address="275 Rue Notre-Dame Est, Montréal")
    assert url is not None
    assert "query=" in url
    assert "Notre-Dame" in url or "Notre" in url


def test_google_maps_url_missing_returns_none():
    assert google_maps_url() is None
    assert google_maps_url(address="  ") is None
    assert google_maps_url(latitude=45.5) is None


def test_google_maps_directions_url():
    url = google_maps_directions_url(45.51, -73.55, 45.5088, -73.5617)
    assert url.startswith("https://www.google.com/maps/dir/?api=1&")
    assert "origin=" in url
    assert "destination=" in url
    assert "45.51" in url
    assert "45.5088" in url


def test_attach_maps_pin_coords():
    row = attach_maps_pin({"id": 1, "latitude": 45.5, "longitude": -73.5})
    assert row["google_maps_url"].startswith("https://www.google.com/maps/search/")
    assert row["id"] == 1
    assert row["openstreetmap_url"] == "https://www.openstreetmap.org/?mlat=45.5&mlon=-73.5#map=17/45.5/-73.5"


def test_osm_invalid_coordinates():
    assert openstreetmap_url(float("nan"), -73.5) is None
    assert openstreetmap_url(91, -73.5) is None
    assert openstreetmap_url(None, None) is None


def test_osm_embed():
    url = openstreetmap_embed_url(45.5088, -73.5541, 800)
    assert url.startswith("https://www.openstreetmap.org/export/embed.html?bbox=")
    assert "marker=45.5088,-73.5541" in url


def test_attach_maps_pin_address_key():
    row = attach_maps_pin(
        {"titre": "FÃªte", "adresse_principale": "1 Place Ville-Marie"},
        address_key="adresse_principale",
    )
    assert "google_maps_url" in row
    assert "Ville-Marie" in row["google_maps_url"] or "Place" in row["google_maps_url"]


def test_attach_maps_pin_no_location():
    row = attach_maps_pin({"id": 1})
    assert "google_maps_url" not in row


def test_attach_nearby_maps_nearest_only_directions():
    items = [
        {"name": "A", "latitude": 45.51, "longitude": -73.55, "distance_m": 10},
        {"name": "B", "latitude": 45.52, "longitude": -73.56, "distance_m": 200},
    ]
    enriched, nearest = attach_nearby_maps(items, query_lat=45.50, query_lon=-73.54)
    assert len(enriched) == 2
    assert enriched[0]["google_maps_url"]
    assert enriched[1]["google_maps_url"]
    assert "google_maps_directions_url" in enriched[0]
    assert "google_maps_directions_url" not in enriched[1]
    assert nearest == enriched[0]["google_maps_directions_url"]
    assert nearest is not None
    assert nearest.startswith("https://www.google.com/maps/dir/")


def test_attach_nearby_maps_avis_keys():
    items = [{"nearest_lat": 45.51, "nearest_lon": -73.55}]
    enriched, nearest = attach_nearby_maps(
        items,
        query_lat=45.50,
        query_lon=-73.54,
        lat_key="nearest_lat",
        lon_key="nearest_lon",
    )
    assert enriched[0]["google_maps_url"]
    assert nearest is not None
