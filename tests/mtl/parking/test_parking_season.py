"""Tests snow / parking déneigement season heuristic."""

from __future__ import annotations

from datetime import date

from helpers.mtl import parking_season


def test_mid_winter_in_season():
    body = parking_season.parking_season_for_day(date(2026, 1, 15))
    assert body["in_season"] is True
    assert body["season_label"] == "2025-2026"
    assert body["season_start"] == "2025-11-01"
    assert body["season_end"] == "2026-04-15"


def test_november_start_in_season():
    body = parking_season.parking_season_for_day(date(2025, 11, 1))
    assert body["in_season"] is True
    assert body["season_label"] == "2025-2026"


def test_april_15_still_in_season():
    body = parking_season.parking_season_for_day(date(2026, 4, 15))
    assert body["in_season"] is True
    assert body["season_label"] == "2025-2026"


def test_april_16_out_of_season_next_label():
    body = parking_season.parking_season_for_day(date(2026, 4, 16))
    assert body["in_season"] is False
    assert body["season_label"] == "2026-2027"
    assert body["season_start"] == "2026-11-01"
    assert body["season_end"] == "2027-04-15"


def test_july_out_of_season():
    body = parking_season.parking_season_for_day(date(2026, 7, 16))
    assert body["in_season"] is False
    assert body["season_label"] == "2026-2027"


def test_build_status_includes_urls():
    data = parking_season.build_parking_season_status(
        date="2026-07-16",
        timezone_name="America/Toronto",
    )
    assert data["in_season"] is False
    assert "stationnements-deneigement" in data["portal_url"]
    assert "vmtl-stationnements-deneigement" in data["dq_url"]
    assert data["time_source"] == "agent"
