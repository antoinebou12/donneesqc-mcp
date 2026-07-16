"""Preview intelligent d'une ressource (headers + 5 lignes)."""

import logging

from helpers.common import ckan_api
from helpers.common.config import DQ_API_URL
from helpers.common.response import error, ok
from tools import mcp

logger = logging.getLogger(__name__)


@mcp.tool(name="qc_preview_resource")
async def preview_resource(resource_id: str) -> str:
    """Apercu rapide d'une ressource : schema (colonnes + types) et 5 premieres lignes.

    Fonctionne pour les ressources DataStore. Pour les ressources non-DataStore,
    utilisez download_resource avec max_rows=5.

    Parameters:
        resource_id: ID de la ressource.
    """
    try:
        # Recuperer les 5 premieres lignes via DataStore
        result = await ckan_api.datastore_search(
            DQ_API_URL,
            resource_id=resource_id,
            limit=5,
            offset=0,
        )

        fields = [
            {"name": f["id"], "type": f.get("type", "unknown")} for f in result.get("fields", []) if f["id"] != "_id"
        ]

        records = result.get("records", [])
        # Nettoyer _id des records
        clean_records = [{k: v for k, v in r.items() if k != "_id"} for r in records]

        return ok(
            {
                "resource_id": resource_id,
                "total_rows": result.get("total", 0),
                "num_columns": len(fields),
                "schema": fields,
                "sample_rows": clean_records,
                "tip": "Utilisez query_resource_data ou query_resource_sql pour interroger les donnees.",
            },
            source="donnees_quebec",
            resource_id=resource_id,
        )
    except Exception:
        logger.exception("Erreur dans preview_resource")
        return error(
            f"Impossible de previsualiser la ressource '{resource_id}'. "
            "Verifiez que datastore_active=true via get_resource_info."
        )
