"""Liste des organisations publiant sur Données Québec."""

import logging

from helpers.common import ckan_api
from helpers.common.config import DQ_API_URL
from helpers.common.response import error, ok
from tools import mcp

logger = logging.getLogger(__name__)


@mcp.tool(name="qc_list_organizations")
async def list_organizations(query: str | None = None) -> str:
    """Liste les organisations publiant des données sur Données Québec.

    Inclut les ministères du Québec, les villes, les sociétés d'État
    et autres organismes publics. Triées par nombre de jeux publiés.

    Parameters:
        query: Filtre optionnel sur le nom (ex: 'montreal', 'santé').
    """
    try:
        orgs = await ckan_api.organization_list(DQ_API_URL, all_fields=True)

        if query:
            q_lower = query.lower()
            orgs = [
                o for o in orgs if q_lower in o.get("display_name", "").lower() or q_lower in o.get("name", "").lower()
            ]

        summary = [
            {
                "id": org.get("name"),
                "title": org.get("display_name") or org.get("title"),
                "num_datasets": org.get("package_count", 0),
                "description": (org.get("description") or "")[:200],
            }
            for org in orgs
        ]

        summary.sort(key=lambda x: x["num_datasets"], reverse=True)

        return ok(
            {"total": len(summary), "organizations": summary[:100]},
            source="donnees_quebec",
        )
    except Exception:
        logger.exception("Erreur dans list_organizations")
        return error("Impossible de lister les organisations.")
