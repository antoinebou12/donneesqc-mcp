"""Enregistrement des outils MCP.

Chaque outil est defini dans un sous-paquet de domaine (qc/, mtl/, common/)
et enregistre ici sur l'instance FastMCP partagee.
"""

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from helpers.common.config import MCP_HOST, MCP_JSON_RESPONSE, MCP_PORT, MCP_STATELESS_HTTP

mcp = FastMCP(
    name="donneesqc-mcp",
    host=MCP_HOST,
    port=MCP_PORT,
    stateless_http=MCP_STATELESS_HTTP,
    json_response=MCP_JSON_RESPONSE,
    instructions="""Tu es un assistant specialise dans les donnees ouvertes du Quebec.
Les outils MCP sont prefixes par domaine pour faciliter la recherche :
- qc_* : Donnees Quebec (CKAN), acces donnees, intelligence
- qc_geo_* : IGO geospatial, geocodage Adresses Quebec, coordonnees
- qc_oqlf_* : Vitrine linguistique OQLF
- qc_nosorigines_* : genealogie NosOrigines
- qc_hydro_* : Info-pannes Hydro-Quebec (etat du service)
- mtl_* : catalogue Ville de Montreal (CKAN)
- mtl_murales_* : murales financees Montreal
- mtl_labicyclette_* : compteurs / La bicyclette
- mtl_collecte_* : Collecte MTL (dechets, ecocentres)
- mtl_avis_* : avis et alertes Ville de Montreal
- mtl_parcs_* / mtl_bixi_* / mtl_qualo_* : parcs, BIXI, qualite de l'eau (QUALO) a proximite
- mtl_neighborhood_briefing : briefing de quartier (Hydro + avis + QUALO + parcs + BIXI)
- mtl_piknic_* / mtl_jazzfest_* : festivals Piknic et Jazz Fest Montreal
- mtl_evenements_* : calendrier evenements publics (vmtl-evenements-publics)
- mtl_calendar_week : agenda semaine (festivals + evenements + avis)
- mtl_events_soon : evenements a venir (festivals + civiques, fenetre heures)
- common_* : version, contexte utilisateur (date/GPS/IP), catalogue d'exemples

Sources : donneesquebec.ca, donnees.montreal.ca, IGO/iCherche,
vitrinelinguistique.oqlf.gouv.qc.ca, nosorigines.qc.ca,
labicyclette.ca, collectemtl.ca, mtlmurales.ca, montreal.ca/avis-et-alertes,
piknicelectronik.com, montrealjazzfest.com, infopannes.solutions.hydroquebec.com,
gbfs.velobixi.com.

Conseils :
1. Prefere qc_find_and_query pour un acces rapide en une seule etape
2. Ou commence par qc_search_datasets / mtl_search_datasets
3. Utilise qc_auto_detect_resource pour trouver la meilleure ressource
4. Utilise qc_preview_resource pour un apercu schema + donnees
5. Verifie datastore_active avant qc_query_resource_data (sinon qc_download_resource)
6. Pour le SQL : qc_suggest_sql puis qc_query_resource_sql
7. Pour les murales : mtl_murales_search / mtl_murales_get / mtl_murales_nearby
8. Pour les avis/alertes pres d'une adresse : mtl_avis_nearby
9. Pour un briefing multi-domaines autour d'une adresse : mtl_neighborhood_briefing
10. Pour Piknic / Jazz Fest : mtl_piknic_search* / mtl_jazzfest_search_*
11. Pour les evenements publics : mtl_evenements_search (Donnees Quebec)
12. Pour l'agenda de la semaine : mtl_calendar_week (GCal + calendar_ascii)
13. Pour ce qui arrive bientot : mtl_events_soon (passe GPS/date telephone si possible)
14. Pour le contexte date/GPS/IP : common_get_context (jamais l'IP du serveur)
15. Pour une panne a une adresse : qc_hydro_outage_status
16. Outils unitaires a proximite : mtl_qualo_nearby / mtl_parcs_nearby / mtl_bixi_nearby
17. Cite toujours la source officielle dans les reponses
""",
)


@mcp.custom_route("/health", methods=["GET"])
async def health(_request: Request) -> JSONResponse:
    """Sonde de sante pour Docker / load balancers."""
    return JSONResponse({"status": "ok", "service": "donneesqc-mcp"})


def register_all_tools() -> None:
    """Importe tous les modules tools pour declencher l'enregistrement @mcp.tool()."""
    import importlib

    modules = (
        # common
        "tools.common.get_version",
        "tools.common.get_context",
        "tools.common.list_tools_with_examples",
        # qc
        "tools.qc.search_datasets",
        "tools.qc.get_dataset_info",
        "tools.qc.list_dataset_resources",
        "tools.qc.get_resource_info",
        "tools.qc.query_resource_data",
        "tools.qc.query_resource_sql",
        "tools.qc.list_organizations",
        "tools.qc.get_organization_info",
        "tools.qc.get_catalog_stats",
        "tools.qc.download_resource",
        "tools.qc.preview_resource",
        "tools.qc.find_and_query",
        "tools.qc.suggest_sql",
        "tools.qc.compare_datasets",
        "tools.qc.auto_detect_resource",
        "tools.qc.geo.list_geospatial_layers",
        "tools.qc.geo.get_geospatial_features",
        "tools.qc.geo.describe_geospatial_layer",
        "tools.qc.geo.get_map_url",
        "tools.qc.geo.geocode",
        "tools.qc.geo.reverse_geocode",
        "tools.qc.geo.convert_coordinates",
        "tools.qc.geo.spatial_intersection",
        "tools.qc.oqlf.search_vitrine_linguistique",
        "tools.qc.oqlf.get_vitrine_entry",
        "tools.qc.nosorigines.search_nosorigines",
        "tools.qc.nosorigines.get_person",
        "tools.qc.nosorigines.get_ancestors",
        "tools.qc.hydro.outage_status",
        # mtl
        "tools.mtl.search_datasets",
        "tools.mtl.query_data",
        "tools.mtl.query_sql",
        "tools.mtl.murales.search_murales",
        "tools.mtl.murales.get_murale",
        "tools.mtl.murales.list_murales_nearby",
        "tools.mtl.murales.get_random_murale",
        "tools.mtl.murales.list_murales_facet",
        "tools.mtl.labicyclette.get_labicyclette_overview",
        "tools.mtl.labicyclette.list_labicyclette_counters",
        "tools.mtl.labicyclette.get_labicyclette_counter",
        "tools.mtl.labicyclette.get_labicyclette_boroughs",
        "tools.mtl.labicyclette.list_labicyclette_construction",
        "tools.mtl.collecte.find_montreal_waste_collection",
        "tools.mtl.collecte.find_montreal_ecocentres",
        "tools.mtl.collecte.get_montreal_borough_waste_stats",
        "tools.mtl.avis.find_avis_nearby",
        "tools.mtl.neighborhood.briefing",
        "tools.mtl.parcs.find_parcs_nearby",
        "tools.mtl.bixi.find_bixi_nearby",
        "tools.mtl.qualo.find_qualo_nearby",
        "tools.mtl.festivals.search_piknic_off",
        "tools.mtl.festivals.search_piknic",
        "tools.mtl.festivals.search_piknic_petit",
        "tools.mtl.festivals.search_jazzfest_free",
        "tools.mtl.festivals.search_jazzfest_paid",
        "tools.mtl.evenements.search_evenements",
        "tools.mtl.calendar.week",
        "tools.mtl.events.events_soon",
    )
    for name in modules:
        importlib.import_module(name)
