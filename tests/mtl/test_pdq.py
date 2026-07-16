"""Tests du dictionnaire SPVM PDQ."""

from helpers.mtl.pdq import enrich_records, pdq_label, pdq_name


def test_pdq_label_known():
    assert pdq_label(38) == "38 (Plateau-Mont-Royal)"
    assert pdq_label("21") == "21 (Centre-Sud / Ville-Marie Est)"
    assert pdq_label("7.0") == "7 (Saint-Laurent)"


def test_pdq_label_unknown():
    assert pdq_label(999) == "999"
    assert pdq_label("") == ""
    assert pdq_label(None) == ""


def test_pdq_name_full_title():
    assert pdq_name(38) == "Le Plateau-Mont-Royal"
    assert "Centre-Sud" in (pdq_name(21) or "")
    assert pdq_name(999) is None


def test_enrich_records_adds_labels():
    records = [
        {"PDQ": "38", "total": 100},
        {"ARROND": "x", "total": 1},
        {"PDQ": "", "total": 0},
    ]
    out = enrich_records(records)
    assert out[0]["pdq_label"] == "38 (Plateau-Mont-Royal)"
    assert out[0]["pdq_name"] == "Le Plateau-Mont-Royal"
    assert out[0]["total"] == 100
    assert "pdq_label" not in out[1]
    assert "pdq_label" not in out[2]
    # Originals untouched
    assert "pdq_label" not in records[0]


def test_extract_resource_ids_from_sql():
    from helpers.common.ckan_format import extract_resource_ids_from_sql

    sql = (
        'SELECT "PDQ", COUNT(*) AS total '
        'FROM "c6f482bf-bf0f-4960-8b2f-9982c211addd" '
        'WHERE "PDQ" IS NOT NULL '
        'GROUP BY "PDQ"'
    )
    assert extract_resource_ids_from_sql(sql) == ["c6f482bf-bf0f-4960-8b2f-9982c211addd"]


def test_portal_sql_and_resource_urls():
    from helpers.common.portals import MTL_PORTAL

    sql = 'SELECT 1 FROM "c6f482bf-bf0f-4960-8b2f-9982c211addd"'
    url = MTL_PORTAL.sql_api_url(sql)
    assert "datastore_search_sql?sql=" in url
    assert "donnees.montreal.ca" in url
    assert "c6f482bf" in url

    res = MTL_PORTAL.resource_url("actes-criminels", "c6f482bf-bf0f-4960-8b2f-9982c211addd")
    assert res.endswith("/dataset/actes-criminels/resource/c6f482bf-bf0f-4960-8b2f-9982c211addd")
