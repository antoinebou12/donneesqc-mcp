"""Liste les ressources (fichiers) d'un jeu de données."""

import logging

from helpers.common import ckan_api
from helpers.common.config import DQ_API_URL, DQ_BASE_URL
from helpers.common.response import error, ok
from tools import mcp

logger = logging.getLogger(__name__)


@mcp.tool(name="qc_list_dataset_resources")
async def list_dataset_resources(dataset_id: str) -> str:
    """Liste les fichiers et ressources d'un jeu de données Données Québec.

    Retourne format, taille, disponibilité DataStore et URL de chaque ressource.

    Parameters:
        dataset_id: Identifiant ou slug du jeu de données.
    """
    try:
        pkg = await ckan_api.package_show(DQ_API_URL, dataset_id)
        resources = [
            {
                "id": res.get("id"),
                "name": res.get("name") or res.get("description", "Sans nom"),
                "format": res.get("format", "inconnu"),
                "size_bytes": res.get("size"),
                "datastore_active": res.get("datastore_active", False),
                "url": res.get("url"),
                "last_modified": res.get("last_modified"),
            }
            for res in pkg.get("resources", [])
        ]

        return ok(
            {"dataset": pkg.get("title"), "total_resources": len(resources), "resources": resources},
            source="donnees_quebec",
            portal_url=f"{DQ_BASE_URL}/dataset/{pkg.get('name')}",
            dataset_id=pkg.get("id"),
            license=pkg.get("license_title"),
            metadata_modified=pkg.get("metadata_modified"),
        )
    except Exception:
        logger.exception("Erreur dans list_dataset_resources")
        return error(f"Impossible de lister les ressources du jeu '{dataset_id}'.")
