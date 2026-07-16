"""Requête SQL sur les données de la Ville de Montréal."""

from helpers.common import ckan_api, ckan_format
from helpers.common.portals import MTL_PORTAL
from helpers.common.tool_call import run_tool
from helpers.mtl.citations import mtl_open_ok
from helpers.mtl.pdq import enrich_records
from tools import mcp


@mcp.tool(name="mtl_query_sql")
async def query_montreal_sql(sql: str) -> str:
    """Requête SQL sur les données de donnees.montreal.ca (lecture seule).

    Mêmes capacités que query_resource_sql mais sur le DataStore montréalais.
    Si les résultats contiennent une colonne PDQ, chaque ligne est enrichie
    avec pdq_label / pdq_name (dictionnaire SPVM).

    Parameters:
        sql: Requête SELECT SQL. Les tables sont les resource_id montréalais.
    """

    async def _run() -> str:
        result = await ckan_api.datastore_search_sql(MTL_PORTAL.api_url, sql)
        payload = ckan_format.datastore_payload(result, include_sql=sql)
        payload["records"] = enrich_records(payload["records"])
        payload["sql_url"] = MTL_PORTAL.sql_api_url(sql)

        resource_ids = ckan_format.extract_resource_ids_from_sql(sql)
        resource_id = resource_ids[0] if resource_ids else None
        dataset_url = MTL_PORTAL.base_url
        if resource_id:
            citation = await ckan_format.resolve_resource_citation(MTL_PORTAL, resource_id)
            dataset_url = ckan_format.attach_citation_fields(payload, citation) or dataset_url

        return mtl_open_ok(
            payload,
            source=MTL_PORTAL.source,
            portal_url=dataset_url,
            resource_id=resource_id,
        )

    return await run_tool(
        "query_montreal_sql",
        _run,
        generic_error="Erreur SQL sur donnees.montreal.ca. Vérifiez la syntaxe et les resource_id.",
    )
