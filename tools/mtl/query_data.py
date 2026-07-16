"""Interroge les données d'une ressource montréalaise."""

from helpers.common import ckan_api, ckan_format
from helpers.common.portals import MTL_PORTAL
from helpers.common.tool_call import run_tool
from helpers.mtl.citations import mtl_open_ok
from helpers.mtl.pdq import enrich_records
from tools import mcp


@mcp.tool(name="mtl_query_data")
async def query_montreal_data(
    resource_id: str,
    question: str | None = None,
    filters: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> str:
    """Interroge les données d'une ressource de la Ville de Montréal via le DataStore.

    Si les résultats contiennent une colonne PDQ, chaque ligne est enrichie
    avec pdq_label / pdq_name (dictionnaire SPVM).

    Parameters:
        resource_id: ID de la ressource DataStore montréalaise.
        question: Recherche plein texte.
        filters: Filtres JSON (ex: '{"ARROND": "Le Plateau-Mont-Royal"}').
        page: Numéro de page (défaut 1).
        page_size: Lignes par page (1-200, défaut 20).
    """

    async def _run() -> str:
        safe_page, size, offset = ckan_format.paginate(page, page_size, max_size=200)
        filters_dict = ckan_format.parse_filters_json(filters)

        result = await ckan_api.datastore_search(
            MTL_PORTAL.api_url,
            resource_id=resource_id,
            q=question,
            filters=filters_dict,
            limit=size,
            offset=offset,
        )
        payload = ckan_format.datastore_payload(result, page=safe_page, page_size=size)
        payload["records"] = enrich_records(payload["records"])

        citation = await ckan_format.resolve_resource_citation(MTL_PORTAL, resource_id)
        dataset_url = ckan_format.attach_citation_fields(payload, citation) or MTL_PORTAL.base_url

        return mtl_open_ok(
            payload,
            source=MTL_PORTAL.source,
            portal_url=dataset_url,
            resource_id=resource_id,
        )

    return await run_tool(
        "query_montreal_data",
        _run,
        generic_error=f"Impossible d'interroger la ressource montréalaise '{resource_id}'.",
    )
