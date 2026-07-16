"""Meta-introspection : liste tous les outils avec exemples d'utilisation."""

import logging

from helpers.common.response import error, ok
from tools import mcp

logger = logging.getLogger(__name__)

# Cles = noms MCP enregistres (@mcp.tool(name=...))
_TOOL_EXAMPLES: dict[str, dict] = {
    # qc
    "qc_search_datasets": {
        "category": "qc",
        "description": "Rechercher des jeux de donnees sur Donnees Quebec",
        "example": {"query": "pistes cyclables", "organization": "ville-de-montreal"},
    },
    "qc_get_dataset_info": {
        "category": "qc",
        "description": "Metadonnees completes d'un jeu de donnees",
        "example": {"dataset_id": "vmtl-evenements-publics"},
    },
    "qc_list_dataset_resources": {
        "category": "qc",
        "description": "Liste les fichiers d'un jeu de donnees",
        "example": {"dataset_id": "vmtl-evenements-publics"},
    },
    "qc_get_resource_info": {
        "category": "qc",
        "description": "Detail d'une ressource specifique",
        "example": {"resource_id": "6decf611-6f11-4f34-bb36-324d804c9bad"},
    },
    "qc_get_organization_info": {
        "category": "qc",
        "description": "Detail d'une organisation",
        "example": {"organization_id": "ville-de-montreal"},
    },
    "qc_list_organizations": {
        "category": "qc",
        "description": "Liste des organisations du catalogue",
        "example": {"query": "ville"},
    },
    "qc_get_catalog_stats": {
        "category": "qc",
        "description": "Statistiques globales + top organisations + thèmes (groupes)",
        "example": {"organization": "ville-de-montreal"},
    },
    "qc_query_resource_data": {
        "category": "qc",
        "description": "Interroger les donnees d'une ressource DataStore",
        "example": {"resource_id": "<resource_id>", "page_size": 10},
    },
    "qc_query_resource_sql": {
        "category": "qc",
        "description": "Requete SQL sur le DataStore",
        "example": {"sql": 'SELECT "ville", COUNT(*) as total FROM "<resource_id>" GROUP BY "ville" LIMIT 10'},
    },
    "qc_download_resource": {
        "category": "qc",
        "description": "Telecharger une ressource non-DataStore (CSV, JSON, GeoJSON)",
        "example": {"resource_id": "<resource_id>", "max_rows": 50},
    },
    "qc_preview_resource": {
        "category": "qc",
        "description": "Apercu rapide : schema + 5 premieres lignes",
        "example": {"resource_id": "<resource_id>"},
    },
    "qc_find_and_query": {
        "category": "qc",
        "description": "Recherche + interrogation en un seul appel",
        "example": {"query": "actes criminels montreal", "page_size": 5},
    },
    "qc_suggest_sql": {
        "category": "qc",
        "description": "Genere des squelettes SQL a partir du schema",
        "example": {"resource_id": "<resource_id>"},
    },
    "qc_compare_datasets": {
        "category": "qc",
        "description": "Compare deux jeux de donnees",
        "example": {
            "dataset_id_1": "vmtl-actes-criminels",
            "dataset_id_2": "vmtl-interventions-service-securite-incendie-montreal",
        },
    },
    "qc_auto_detect_resource": {
        "category": "qc",
        "description": "Trouve le meilleur resource_id a partir d'un nom",
        "example": {"dataset_name": "vmtl-actes-criminels"},
    },
    # qc/geo
    "qc_geo_list_layers": {
        "category": "qc/geo",
        "description": "Liste les couches WFS/WMS disponibles",
        "example": {"service": "wfs", "query": "casernes"},
    },
    "qc_geo_get_features": {
        "category": "qc/geo",
        "description": "Recupere les entites d'une couche WFS",
        "example": {"layer_name": "ms:CASERNE", "max_features": 10},
    },
    "qc_geo_describe_layer": {
        "category": "qc/geo",
        "description": "Schema d'une couche WFS",
        "example": {"layer_name": "ms:CASERNE"},
    },
    "qc_geo_get_map_url": {
        "category": "qc/geo",
        "description": "Genere une URL de carte WMS",
        "example": {"layers": "ms:CASERNE", "bbox": "-73.7,45.4,-73.4,45.6"},
    },
    "qc_geo_geocode": {
        "category": "qc/geo",
        "description": "Adresse -> coordonnees (lat/lng)",
        "example": {"address": "900 Boulevard Rene-Levesque, Quebec"},
    },
    "qc_geo_reverse_geocode": {
        "category": "qc/geo",
        "description": "Coordonnees -> adresse quebecoise",
        "example": {"latitude": 45.5017, "longitude": -73.5673},
    },
    "qc_geo_convert_coordinates": {
        "category": "qc/geo",
        "description": "Conversion EPSG:32198 (Lambert) <-> EPSG:4326 (WGS84)",
        "example": {"x": -73.5673, "y": 45.5017, "from_crs": "EPSG:4326", "to_crs": "EPSG:32198"},
    },
    "qc_geo_spatial_intersection": {
        "category": "qc/geo",
        "description": "Quel arrondissement/region contient ce point?",
        "example": {
            "latitude": 45.5017,
            "longitude": -73.5673,
            "layer_type": "regions_administratives",
        },
    },
    # qc/oqlf
    "qc_oqlf_search": {
        "category": "qc/oqlf",
        "description": "Recherche BDL/GDT dans la Vitrine linguistique OQLF",
        "example": {"query": "Quebec", "include_bdl": True, "include_gdt": True},
    },
    "qc_oqlf_get_entry": {
        "category": "qc/oqlf",
        "description": "Extrait d'une fiche Vitrine linguistique",
        "example": {"url": "https://vitrinelinguistique.oqlf.gouv.qc.ca/..."},
    },
    # qc/nosorigines
    "qc_nosorigines_search": {
        "category": "qc/nosorigines",
        "description": "Recherche personnes/couples sur NosOrigines",
        "example": {"last_name": "Champlain", "first_name": "Samuel", "match_mode": "starting"},
    },
    "qc_nosorigines_get_person": {
        "category": "qc/nosorigines",
        "description": "Fiche personne NosOrigines (parents, conjoint, enfants)",
        "example": {"pid": "781"},
    },
    "qc_nosorigines_get_ancestors": {
        "category": "qc/nosorigines",
        "description": "Remonte parents / grands-parents NosOrigines",
        "example": {"pid": "781", "generations": 2},
    },
    # qc/hydro
    "qc_hydro_outage_status": {
        "category": "qc/hydro",
        "description": "Etat du service electrique Hydro-Quebec (Info-pannes)",
        "example": {"address": "1 Place Ville-Marie, Montreal"},
    },
    # mtl
    "mtl_search_datasets": {
        "category": "mtl",
        "description": "Rechercher sur le portail de la Ville de Montreal",
        "example": {"query": "arbres"},
    },
    "mtl_query_data": {
        "category": "mtl",
        "description": "Interroger les donnees de Montreal",
        "example": {"resource_id": "<resource_id>", "page_size": 10},
    },
    "mtl_query_sql": {
        "category": "mtl",
        "description": "Requete SQL sur les donnees de Montreal",
        "example": {"sql": 'SELECT "ARROND", COUNT(*) as nb FROM "<resource_id>" GROUP BY "ARROND" LIMIT 10'},
    },
    # mtl/murales
    "mtl_murales_search": {
        "category": "mtl/murales",
        "description": "Recherche murales financees (artiste, arrondissement, annee)",
        "example": {"arrondissement": "Plateau", "annee_min": "2020", "page_size": 5},
    },
    "mtl_murales_get": {
        "category": "mtl/murales",
        "description": "Detail d'une murale par id",
        "example": {"murale_id": "307"},
    },
    "mtl_murales_nearby": {
        "category": "mtl/murales",
        "description": "Murales a proximite d'un point GPS",
        "example": {"latitude": 45.5088, "longitude": -73.5617, "radius_m": 800},
    },
    "mtl_murales_random": {
        "category": "mtl/murales",
        "description": "Tirage aleatoire de murales",
        "example": {"arrondissement": "Ville-Marie", "count": 2},
    },
    "mtl_murales_facet": {
        "category": "mtl/murales",
        "description": "Facettes artiste / arrondissement / annee",
        "example": {"facet": "arrondissement"},
    },
    # mtl/labicyclette
    "mtl_labicyclette_overview": {
        "category": "mtl/labicyclette",
        "description": "KPIs overview (cartes Total/Active/Daily avg)",
        "example": {},
    },
    "mtl_labicyclette_list_counters": {
        "category": "mtl/labicyclette",
        "description": "Liste compteurs + chart map_points",
        "example": {"arrondissement": "Ville-Marie", "limit": 20},
    },
    "mtl_labicyclette_get_counter": {
        "category": "mtl/labicyclette",
        "description": "Serie volume + resume (meteo optionnelle)",
        "example": {
            "instance": "100003032",
            "from_date": "2025-07-01",
            "to_date": "2025-07-16",
            "include_weather": False,
        },
    },
    "mtl_labicyclette_boroughs": {
        "category": "mtl/labicyclette",
        "description": "Volumes par arrondissement (rangs; chart API optionnel)",
        "example": {},
    },
    "mtl_labicyclette_list_construction": {
        "category": "mtl/labicyclette",
        "description": "Chantiers actifs (filtres) + map_points",
        "example": {"status": "blocked", "limit": 10, "min_severity": 50},
    },
    # mtl/collecte
    "mtl_collecte_find_waste": {
        "category": "mtl/collecte",
        "description": "Calendrier de collecte des dechets par adresse (Collecte MTL)",
        "example": {"address": "1 Place Ville-Marie, Montreal"},
    },
    "mtl_collecte_find_ecocentres": {
        "category": "mtl/collecte",
        "description": "Ecocentres les plus proches (lat/lng)",
        "example": {"lat": 45.5088, "lng": -73.5541, "limit": 3},
    },
    "mtl_collecte_borough_waste_stats": {
        "category": "mtl/collecte",
        "description": "Bilan massique / taux de recuperation par arrondissement",
        "example": {"address": "1 Place Ville-Marie, Montreal"},
    },
    # mtl/avis
    "mtl_avis_nearby": {
        "category": "mtl/avis",
        "description": "Avis/alertes actifs a une date, proches d'une adresse",
        "example": {
            "address": "800 Rue De La Gauchetiere Ouest, Montreal",
            "date": "2026-07-16",
            "radius_m": 800,
            "limit": 10,
        },
    },
    # mtl/parcs / bixi / qualo
    "mtl_parcs_nearby": {
        "category": "mtl/parcs",
        "description": "Parcs / places publiques proches (GeoJSON espaces verts)",
        "example": {
            "address": "275 Rue Notre-Dame Est, Montreal",
            "radius_m": 800,
            "limit": 10,
        },
    },
    "mtl_bixi_nearby": {
        "category": "mtl/bixi",
        "description": "Stations BIXI proches (GBFS live)",
        "example": {
            "address": "275 Rue Notre-Dame Est, Montreal",
            "radius_m": 600,
            "limit": 10,
        },
    },
    "mtl_qualo_nearby": {
        "category": "mtl/qualo",
        "description": "Mesures QUALO (qualite eau en rive) proches",
        "example": {
            "address": "275 Rue Notre-Dame Est, Montreal",
            "radius_m": 5000,
            "limit": 8,
        },
    },
    "mtl_neighborhood_briefing": {
        "category": "mtl/neighborhood",
        "description": "Briefing de quartier: Hydro + avis + QUALO + parcs + BIXI",
        "example": {
            "address": "275 Rue Notre-Dame Est, Montreal",
            "date": "2026-07-16",
            "avis_radius_m": 1000,
            "parks_radius_m": 300,
            "bixi_radius_m": 400,
            "qualo_radius_m": 1500,
            "limit": 10,
        },
    },
    # mtl/festivals
    "mtl_piknic_search_off": {
        "category": "mtl/festivals",
        "description": "Programmation OfF Piknic (liste ou filtre artiste/date)",
        "example": {"query": "", "limit": 10},
    },
    "mtl_piknic_search": {
        "category": "mtl/festivals",
        "description": "Programmation Piknic (serie principale)",
        "example": {"query": "Mandragora"},
    },
    "mtl_piknic_search_petit": {
        "category": "mtl/festivals",
        "description": "Programmation Petit Piknic",
        "example": {"date": "2026-07-19"},
    },
    "mtl_jazzfest_search_free": {
        "category": "mtl/festivals",
        "description": "Concerts gratuits Festival de Jazz de Montreal",
        "example": {"query": "", "limit": 25},
    },
    "mtl_jazzfest_search_paid": {
        "category": "mtl/festivals",
        "description": "Concerts payants Festival de Jazz de Montreal",
        "example": {"query": "Isaiah Collier"},
    },
    "mtl_evenements_search": {
        "category": "mtl/evenements",
        "description": "Evenements publics Montreal (vmtl-evenements-publics, DQ CKAN)",
        "example": {"query": "festival", "date": "2026-07-19", "limit": 10},
    },
    "mtl_calendar_week": {
        "category": "mtl/calendar",
        "description": "Agenda semaine: festivals + evenements + avis (GCal + calendar_ascii)",
        "example": {
            "week_start": "2026-07-13",
            "address": "800 Rue De La Gauchetiere Ouest, Montreal",
            "include_avis": True,
            "limit_per_source": 15,
        },
    },
    "mtl_events_soon": {
        "category": "mtl/events",
        "description": "Evenements a venir (festivals + civiques) dans les prochaines heures",
        "example": {
            "hours": 24,
            "latitude": 45.5088,
            "longitude": -73.5617,
            "limit": 15,
        },
    },
    # common
    "common_get_version": {
        "category": "common",
        "description": "Version et capacites du serveur MCP",
        "example": {},
    },
    "common_get_context": {
        "category": "common",
        "description": "Date/heure + GPS agent ou IP client (jamais IP serveur MCP)",
        "example": {
            "latitude": 45.5088,
            "longitude": -73.5617,
            "timezone": "America/Toronto",
        },
    },
    "common_list_tools_with_examples": {
        "category": "common",
        "description": "Liste tous les outils avec exemples (cet outil)",
        "example": {"category": "qc/geo"},
    },
}


@mcp.tool(name="common_list_tools_with_examples")
async def list_tools_with_examples(category: str | None = None) -> str:
    """Liste tous les outils MCP disponibles avec descriptions et exemples.

    Categories : qc, qc/geo, qc/oqlf, qc/nosorigines, qc/hydro, mtl, mtl/murales,
    mtl/labicyclette, mtl/collecte, mtl/avis, mtl/parcs, mtl/bixi, mtl/qualo,
    mtl/festivals, mtl/evenements, mtl/calendar, mtl/events, common.

    Parameters:
        category: Filtrer par categorie (ex. qc, mtl/murales, qc/geo).
    """
    try:
        tools = _TOOL_EXAMPLES

        if category:
            cat_lower = category.lower()
            tools = {k: v for k, v in tools.items() if v["category"].lower() == cat_lower}

        categories: dict[str, list] = {}
        for name, info in sorted(tools.items()):
            cat = info["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(
                {
                    "tool": name,
                    "description": info["description"],
                    "example_params": info["example"],
                }
            )

        return ok(
            {
                "total_tools": len(tools),
                "categories": categories,
                "tip": "Appelez un outil directement avec les parametres de l'exemple.",
            },
            source="donneesqc_mcp",
        )
    except Exception:
        logger.exception("Erreur dans list_tools_with_examples")
        return error("Impossible de lister les outils.")
