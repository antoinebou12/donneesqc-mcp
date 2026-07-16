"""Tool composite : search -> resources -> query en un seul appel."""

from helpers.common import ckan_api, ckan_format
from helpers.common.portals import DQ_PORTAL
from helpers.common.response import error, ok
from helpers.common.tool_call import run_tool
from tools import mcp


@mcp.tool(name="qc_find_and_query")
async def find_and_query(
    query: str,
    question: str | None = None,
    page_size: int = 5,
    prefer_format: str = "CSV",
) -> str:
    """Recherche un jeu de donnees, trouve une ressource DataStore, et interroge les donnees en un seul appel.

    Enchaine automatiquement : search_datasets -> list_resources -> query_resource_data.
    Evite 3 allers-retours LLM.

    Parameters:
        query: Termes de recherche (ex: 'pistes cyclables montreal').
        question: Recherche plein texte dans les donnees (optionnel).
        page_size: Nombre de lignes de donnees a retourner (defaut 5).
        prefer_format: Format prefere pour la ressource (defaut CSV).
    """

    async def _run() -> str:
        search_result = await ckan_api.package_search(DQ_PORTAL.api_url, query=query, rows=5)
        datasets = search_result.get("results", [])
        if not datasets:
            return error(f"Aucun jeu de donnees trouve pour '{query}'.")

        selected_dataset = None
        selected_resource = None
        for pkg in datasets:
            chosen = ckan_format.select_datastore_resource(pkg.get("resources", []), prefer_format=prefer_format)
            if chosen:
                selected_dataset = pkg
                selected_resource = chosen
                break

        if not selected_resource or selected_dataset is None:
            return ok(
                {
                    "search_results": len(datasets),
                    "datasets": [
                        {
                            "id": pkg.get("id"),
                            "name": pkg.get("name"),
                            "title": pkg.get("title"),
                            "resources": ckan_format.summarize_resources(pkg),
                        }
                        for pkg in datasets[:3]
                    ],
                    "note": (
                        "Aucune ressource DataStore trouvee."
                        " Utilisez download_resource pour les ressources non-DataStore."
                    ),
                },
                source=DQ_PORTAL.source,
                portal_url=DQ_PORTAL.base_url,
            )

        data_result = await ckan_api.datastore_search(
            DQ_PORTAL.api_url,
            resource_id=selected_resource["id"],
            q=question,
            limit=min(page_size, 100),
        )
        org = selected_dataset.get("organization") or {}
        return ok(
            {
                "dataset": {
                    "id": selected_dataset.get("id"),
                    "title": selected_dataset.get("title"),
                    "organization": org.get("title", "") if isinstance(org, dict) else "",
                    "url": DQ_PORTAL.dataset_url(selected_dataset.get("name")),
                },
                "resource": {
                    "id": selected_resource.get("id"),
                    "name": selected_resource.get("name"),
                    "format": selected_resource.get("format"),
                },
                "data": ckan_format.datastore_payload(data_result),
            },
            source=DQ_PORTAL.source,
            portal_url=DQ_PORTAL.base_url,
            dataset_id=selected_dataset.get("id"),
            resource_id=selected_resource.get("id"),
        )

    return await run_tool(
        "find_and_query",
        _run,
        generic_error=f"Erreur lors de la recherche et interrogation pour '{query}'.",
    )
