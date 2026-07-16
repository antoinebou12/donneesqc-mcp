"""Interroge les données d'une ressource via le DataStore CKAN."""

from helpers.common import ckan_api, ckan_format
from helpers.common.portals import DQ_PORTAL
from helpers.common.response import ok
from helpers.common.tool_call import run_tool
from tools import mcp


@mcp.tool(name="qc_query_resource_data")
async def query_resource_data(
    resource_id: str,
    question: str | None = None,
    filters: str | None = None,
    fields: str | None = None,
    sort: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> str:
    """Interroge les données d'une ressource Données Québec via le DataStore.

    Fonctionne pour les CSV/XLSX importés dans le DataStore.
    Vérifiez que 'datastore_active' est True via get_resource_info.

    Workflow recommandé :
    1. search_datasets pour trouver le jeu
    2. list_dataset_resources pour voir les ressources
    3. query_resource_data avec page_size=20 pour aperçu
    4. Pour des analyses avancées, utiliser query_resource_sql

    Parameters:
        resource_id: ID de la ressource DataStore.
        question: Recherche plein texte dans toutes les colonnes.
        filters: Filtres JSON clé-valeur (ex: '{"ville": "Montréal"}').
        fields: Colonnes à retourner (séparées par des virgules).
        sort: Tri (ex: 'population desc').
        page: Numéro de page (défaut 1).
        page_size: Lignes par page (1-200, défaut 20).
    """

    async def _run() -> str:
        safe_page, size, offset = ckan_format.paginate(page, page_size, max_size=200)
        filters_dict = ckan_format.parse_filters_json(filters)
        fields_list = [f.strip() for f in fields.split(",")] if fields else None

        result = await ckan_api.datastore_search(
            DQ_PORTAL.api_url,
            resource_id=resource_id,
            q=question,
            filters=filters_dict,
            fields=fields_list,
            sort=sort,
            limit=size,
            offset=offset,
        )
        return ok(
            ckan_format.datastore_payload(result, page=safe_page, page_size=size),
            source=DQ_PORTAL.source,
            portal_url=DQ_PORTAL.base_url,
            resource_id=resource_id,
        )

    return await run_tool(
        "query_resource_data",
        _run,
        generic_error=f"Impossible d'interroger la ressource '{resource_id}'.",
    )
