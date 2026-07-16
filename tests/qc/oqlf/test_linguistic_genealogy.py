"""Tests pour Vitrine linguistique et NosOrigines."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from helpers.qc.nosorigines import nosorigines_api
from helpers.qc.oqlf import vitrine_api

VITRINE_HTML = """
<html><body>
<main>
  <h2><a href="/fiche/prepositions-quebec">Les prépositions devant un nom de province</a></h2>
  <div>Contenu bdl Préposition devant un nom Avec les noms de genre masculin...</div>
  <h2><a href="/fiche/francais-quebecois">français québécois</a></h2>
  <div>Contenu gdt linguistique Le français parlé dans les provinces...</div>
</main>
</body></html>
"""

VITRINE_ENTRY_HTML = """
<html><body>
<main>
  <h1>Abréviation de Québec</h1>
  <p>Le symbole officiel du nom de la province de Québec est QC.</p>
  <p>On en limite l'emploi à certains contextes précis.</p>
</main>
</body></html>
"""

NOSORIGINES_FORM_HTML = """
<html><body>
<form method="post">
  <input type="hidden" name="__VIEWSTATE" value="vs123" />
  <input type="hidden" name="__VIEWSTATEGENERATOR" value="gen456" />
  <input type="hidden" name="__EVENTVALIDATION" value="ev789" />
</form>
</body></html>
"""

NOSORIGINES_RESULTS_HTML = """
<html><body>
<table>
  <tr>
    <td><a href="GenealogieIndividual.aspx?pid=123">Champlain, Samuel</a></td>
    <td>1574</td>
  </tr>
  <tr>
    <td><a href="Genealogie.aspx?pid=456">Hébert, Louis</a></td>
    <td>1575</td>
  </tr>
</table>
</body></html>
"""


def test_parse_vitrine_search_results():
    results = vitrine_api.parse_search_results(VITRINE_HTML, limit=5)
    assert len(results) == 2
    assert results[0]["title"].startswith("Les prépositions")
    assert results[0]["type"] == "bdl"
    assert "vitrinelinguistique" in results[0]["url"]
    assert results[1]["type"] == "gdt"


def test_parse_vitrine_entry():
    data = vitrine_api.parse_entry(VITRINE_ENTRY_HTML, "https://vitrinelinguistique.oqlf.gouv.qc.ca/fiche/x")
    assert data["title"] == "Abréviation de Québec"
    assert "QC" in data["excerpt"]


def test_extract_aspnet_fields():
    fields = nosorigines_api.extract_aspnet_fields(NOSORIGINES_FORM_HTML)
    assert fields["__VIEWSTATE"] == "vs123"
    assert fields["__VIEWSTATEGENERATOR"] == "gen456"
    assert fields["__EVENTVALIDATION"] == "ev789"


def test_parse_nosorigines_results():
    results = nosorigines_api.parse_search_results(NOSORIGINES_RESULTS_HTML, limit=10)
    assert len(results) == 2
    assert results[0]["name"] == "Champlain, Samuel"
    assert "pid=123" in results[0]["url"]


@pytest.mark.asyncio
async def test_search_vitrine_linguistique_tool():
    mock_data = {
        "query": "Québec",
        "total_returned": 1,
        "results": [
            {
                "title": "t",
                "url": "https://vitrinelinguistique.oqlf.gouv.qc.ca/x",
                "type": "bdl",
                "snippet": "",
            }
        ],
        "source": "https://vitrinelinguistique.oqlf.gouv.qc.ca",
    }
    with patch(
        "helpers.qc.oqlf.vitrine_api.search_vitrine",
        new_callable=AsyncMock,
        return_value=mock_data,
    ):
        from tools.qc.oqlf.search_vitrine_linguistique import search_vitrine_linguistique

        result = json.loads(await search_vitrine_linguistique(query="Québec"))
        assert result["total_returned"] == 1
        assert result["query"] == "Québec"


@pytest.mark.asyncio
async def test_get_vitrine_entry_rejects_foreign_url():
    from tools.qc.oqlf.get_vitrine_entry import get_vitrine_entry

    result = json.loads(await get_vitrine_entry(url="https://evil.example/x"))
    assert "error" in result
