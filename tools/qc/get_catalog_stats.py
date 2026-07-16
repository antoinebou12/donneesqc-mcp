"""Statistiques globales du catalogue Données Québec."""

from helpers.common import ckan_api, ckan_format
from helpers.common.portals import DQ_PORTAL
from helpers.common.response import ok
from helpers.common.tool_call import run_tool
from tools import mcp


@mcp.tool(name="qc_get_catalog_stats")
async def get_catalog_stats(organization: str | None = None) -> str:
    """Statistiques globales du catalogue Données Québec.

    Retourne le nombre total de jeux, d'organisations, le top 10 des
    organisations, et les thèmes (groupes CKAN) avec leurs compteurs.

    Parameters:
        organization: Filtrer les totaux et thèmes par organisation
            (ex. ``ville-de-montreal``). Les top organisations restent globales.
    """

    async def _run() -> str:
        fq = ckan_format.build_package_search_fq(organization=organization)
        all_result = await ckan_api.package_search(
            DQ_PORTAL.api_url,
            query="*:*",
            rows=0,
            fq=fq,
            facet_fields=["groups"],
        )
        orgs = await ckan_api.organization_list(DQ_PORTAL.api_url, all_fields=True)
        top_orgs = sorted(orgs, key=lambda x: x.get("package_count", 0), reverse=True)[:10]

        payload: dict = {
            "total_datasets": all_result.get("count", 0),
            "total_organizations": len(orgs),
            "top_organizations": [
                {"name": o.get("display_name"), "datasets": o.get("package_count", 0)} for o in top_orgs
            ],
            "top_groups": ckan_format.parse_search_facet(all_result, "groups"),
        }
        if organization:
            payload["organization"] = organization

        return ok(payload, source=DQ_PORTAL.source, portal_url=DQ_PORTAL.base_url)

    return await run_tool(
        "get_catalog_stats",
        _run,
        generic_error="Impossible de récupérer les statistiques du catalogue.",
    )
