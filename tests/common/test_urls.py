"""Registry URLs / SOURCES - static source metadata."""

from __future__ import annotations

from helpers.common import config, urls


def test_sources_have_required_fields() -> None:
    for key, info in urls.SOURCES.items():
        assert info["key"] == key
        assert info["label"]
        assert info["portal_url"].startswith("http")
        assert info["source"]


def test_get_source_and_helpers() -> None:
    murales = urls.get_source("murales")
    assert murales["dataset_id"] == urls.MURALES_DATASET_ID
    assert urls.mtl_dataset_url("murales").endswith("/dataset/murales")
    assert urls.dq_dataset_url("vmtl-evenements-publics").endswith("/dataset/vmtl-evenements-publics")
    assert "Données Québec" in urls.source_labels()[0]
    caps = urls.source_capabilities()
    assert caps["murales"] is True
    assert caps["festivals"] is True
    flat = urls.as_flat_urls()
    assert flat["MTL_BASE"] == urls.MTL_BASE
    assert flat["BIXI_STATION_INFO"] == urls.BIXI_STATION_INFO


def test_config_defaults_match_urls() -> None:
    assert config.DQ_API_URL == urls.DQ_API
    assert config.MTL_BASE_URL == urls.MTL_BASE
    assert config.EVENEMENTS_PACKAGE_ID == urls.EVENEMENTS_PACKAGE_ID
    assert config.EVENEMENTS_CSV_RESOURCE_ID == urls.EVENEMENTS_CSV_RESOURCE_ID
    assert config.BIXI_STATION_INFO_URL.endswith("station_information.json")
    assert config.PIKNIC_BASE_URL == urls.PIKNIC_BASE
    assert config.IP_GEO_URL_TEMPLATE == urls.IP_GEO_URL_TEMPLATE
    assert config.DEFAULT_TIMEZONE == "America/Toronto"


def test_festival_portals_use_urls_paths() -> None:
    from helpers.mtl import jazzfest_api, piknic_api

    assert piknic_api.PIKNIC_PROGRAM_PATH == urls.PIKNIC_PROGRAM_PATH
    assert jazzfest_api.JAZZFEST_PROGRAM_PATH == urls.JAZZFEST_PROGRAM_PATH
    expected_piknic = urls.join_portal(config.PIKNIC_BASE_URL, urls.PIKNIC_PROGRAM_PATH)
    expected_jazz = urls.join_portal(config.JAZZFEST_BASE_URL, urls.JAZZFEST_PROGRAM_PATH)
    assert expected_piknic == piknic_api.PORTAL_URL
    assert expected_jazz == jazzfest_api.PORTAL_URL


def test_evenements_ids_from_config() -> None:
    from helpers.mtl import evenements_api

    assert evenements_api.PACKAGE_ID == config.EVENEMENTS_PACKAGE_ID
    assert evenements_api.KNOWN_CSV_RESOURCE_IDS == (config.EVENEMENTS_CSV_RESOURCE_ID,)
