"""Unit tests for shared CKAN format helpers."""

from __future__ import annotations

from helpers.common import ckan_format


def test_build_package_search_fq_org_and_tags():
    assert ckan_format.build_package_search_fq(organization="ville-de-montreal") == "organization:ville-de-montreal"
    assert (
        ckan_format.build_package_search_fq(organization="ville-de-montreal", tags="velo, transport")
        == 'organization:ville-de-montreal AND tags:"velo" AND tags:"transport"'
    )
    assert ckan_format.build_package_search_fq() is None


def test_paginate():
    page, size, start = ckan_format.paginate(2, 50, max_size=100)
    assert (page, size, start) == (2, 50, 50)
    page, size, start = ckan_format.paginate(0, 999, max_size=100)
    assert (page, size, start) == (1, 100, 0)


def test_parse_search_facet_items():
    result = {
        "search_facets": {
            "groups": {
                "items": [
                    {"name": "a", "display_name": "Alpha", "count": 2},
                    {"name": "b", "display_name": "Beta", "count": 9},
                ]
            }
        }
    }
    groups = ckan_format.parse_search_facet(result, "groups")
    assert groups[0] == {"name": "Beta", "datasets": 9}
    assert groups[1] == {"name": "Alpha", "datasets": 2}


def test_parse_search_facet_fallback():
    result = {"facets": {"groups": {"infra": 10, "gov": 3}}}
    groups = ckan_format.parse_search_facet(result, "groups")
    assert groups[0]["name"] == "infra"
    assert groups[0]["datasets"] == 10


def test_attach_citation_fields():
    payload: dict = {}
    url = ckan_format.attach_citation_fields(
        payload,
        {
            "dataset_url": "https://example/ds",
            "resource_url": "https://example/res",
            "dataset_title": "Titre",
        },
    )
    assert url == "https://example/ds"
    assert payload["dataset_title"] == "Titre"
