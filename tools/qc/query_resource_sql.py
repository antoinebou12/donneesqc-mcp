"""Requête SQL directe sur le DataStore - fonctionnalité absente de data.gouv.fr."""

from helpers.common import ckan_api, ckan_format
from helpers.common.portals import DQ_PORTAL
from helpers.common.response import ok
from helpers.common.tool_call import run_tool
from tools import mcp


@mcp.tool(name="qc_query_resource_sql")
async def query_resource_sql(sql: str) -> str:
    """Exécute une requête SQL sur le DataStore de Données Québec (lecture seule).

    Fonctionnalité unique - absente de data.gouv.fr.
    Permet des agrégations (GROUP BY, COUNT, SUM, AVG), des jointures
    entre ressources, des sous-requêtes et du SQL arbitraire.

    Les tables sont référencées par leur resource_id entre guillemets.

    Parameters:
        sql: Requête SQL SELECT (lecture seule).
             Exemple: SELECT "ville", COUNT(*) as total
                      FROM "abc-123-def"
                      GROUP BY "ville"
                      ORDER BY total DESC
                      LIMIT 20
    """

    async def _run() -> str:
        result = await ckan_api.datastore_search_sql(DQ_PORTAL.api_url, sql)
        return ok(
            ckan_format.datastore_payload(result, include_sql=sql),
            source=DQ_PORTAL.source,
            portal_url=DQ_PORTAL.base_url,
        )

    return await run_tool(
        "query_resource_sql",
        _run,
        generic_error="Erreur SQL. Vérifiez la syntaxe et les resource_id utilisés.",
    )
