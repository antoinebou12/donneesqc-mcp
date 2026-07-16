"""Conversion de coordonnees entre EPSG:32198 (Lambert MTQ) et EPSG:4326 (WGS84)."""

import logging

from helpers.common.maps_format import google_maps_url
from helpers.common.response import error, ok
from helpers.qc.geo.coords import lambert_to_wgs84, wgs84_to_lambert
from tools import mcp

logger = logging.getLogger(__name__)


@mcp.tool(name="qc_geo_convert_coordinates")
async def convert_coordinates(
    x: float,
    y: float,
    from_crs: str = "EPSG:4326",
    to_crs: str = "EPSG:32198",
) -> str:
    """Convertit des coordonnees entre EPSG:32198 (Lambert MTQ) et EPSG:4326 (WGS84).

    Le Quebec utilise souvent le systeme Lambert conique conforme (EPSG:32198).
    Cet outil permet de convertir facilement vers/depuis WGS84 (GPS classique).

    Parameters:
        x: Premiere coordonnee (longitude si WGS84, X si Lambert).
        y: Deuxieme coordonnee (latitude si WGS84, Y si Lambert).
        from_crs: Systeme source (EPSG:4326 ou EPSG:32198, defaut EPSG:4326).
        to_crs: Systeme cible (EPSG:32198 ou EPSG:4326, defaut EPSG:32198).
    """
    try:
        valid_crs = {"EPSG:4326", "EPSG:32198"}
        if from_crs not in valid_crs or to_crs not in valid_crs:
            return error(f"CRS non supporte. Valeurs acceptees: {', '.join(valid_crs)}")

        if from_crs == to_crs:
            return error("Les systemes source et cible sont identiques.")

        if from_crs == "EPSG:4326":
            result_x, result_y = wgs84_to_lambert(x, y)
            return ok(
                {
                    "input": {"longitude": x, "latitude": y, "crs": "EPSG:4326 (WGS84)"},
                    "output": {"x": result_x, "y": result_y, "crs": "EPSG:32198 (Lambert MTQ)"},
                },
                source="igo",
            )
        result_x, result_y = lambert_to_wgs84(x, y)
        output: dict[str, float | str] = {
            "longitude": result_x,
            "latitude": result_y,
            "crs": "EPSG:4326 (WGS84)",
        }
        maps = google_maps_url(latitude=result_y, longitude=result_x)
        if maps is not None:
            output["google_maps_url"] = maps
        return ok(
            {
                "input": {"x": x, "y": y, "crs": "EPSG:32198 (Lambert MTQ)"},
                "output": output,
            },
            source="igo",
        )

    except Exception:
        logger.exception("Erreur dans convert_coordinates")
        return error(f"Impossible de convertir les coordonnees ({x}, {y}) de {from_crs} vers {to_crs}.")
