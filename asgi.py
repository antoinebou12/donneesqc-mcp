"""Point d'entrée ASGI pour Vercel (et tout serveur ASGI).

Exporte `app` - Starlette Streamable HTTP - sans écrire sur disque.
Sur Vercel, FastMCP tourne en mode stateless (voir helpers.common.config).
"""

from tools import mcp, register_all_tools

register_all_tools()

app = mcp.streamable_http_app()
