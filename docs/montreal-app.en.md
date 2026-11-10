# Montréal app

The `mtl_show_dashboard` tool opens a dashboard in clients supporting [MCP Apps](https://modelcontextprotocol.io/extensions/apps). It shows weather, BIXI stations, parks and STM stops around a Montréal location.

Example: `mtl_show_dashboard(address="Hôtel de Ville de Montréal", radius_m=800, view="move")`.

The `all`, `daily`, `move` and `out` views select the initial cards. The dashboard adds published 311 requests from the last 30 days, parking restriction signs, seasonal snow-removal lots, road closures and Données Québec tourism listings. Published 311 requests do not confirm an intervention. On-site signage and conditions determine parking rules.

For browser access, run `uv run python main.py`, open [localhost:8000/montreal](http://localhost:8000/montreal), and select Explorer. The browser uses the same tool as the embedded app.

Search accepts a radius of 100 to 3000 metres. Each source has a 25-second timeout after geocoding. A failed source displays an error in its section while other results remain available. Results include source links. STM stops come from the GTFS catalogue and do not include upcoming departures. Weather attribution is Open-Meteo (CC BY 4.0).

The French interface supports small screens and keyboard navigation. The embedded map loads OpenStreetMap, with attribution to its contributors. Each place includes OpenStreetMap and Google Maps links. Embedded tool calls pass through the MCP host, and links use `ui/open-link`. The Python package includes the `ui://mtl-mcp/montreal.html` resource. Resource metadata allows only `https://www.openstreetmap.org` for embedded map frames; hosts without frame support can use the external link.

[Documentation française](montreal-app.md)

## Coverage and dates

The dashboard composes fifteen sections from MCP tools: weather, 311, parking signs, snow-removal lots, roadworks, BIXI, STM, REM, municipal notices, ecocentres, murals, parks, restaurants, tourism and events over the coming seven days.

For 311, it selects thirty days ending on the latest geolocated date published by the queried source. Historical results display their start and end dates and do not describe current conditions. The `mtl_311_nearby` tool searches the current period by default; `use_latest_available=true` selects the published period.

When CIFS is unavailable, roadworks use [Entraves et travaux en cours](https://www.donneesquebec.ca/recherche/dataset/vmtl-info-travaux). Permits covering today's date do not confirm an all-day closure. The card identifies the alternative source.

If the requested radius contains no snow-removal lot, the search expands to five kilometres and displays that change. Results include the source file's season and do not represent live availability. Ecocentres are the closest available and may also fall outside the requested radius. Events use an approximate geographic filter.

## Verify and connect the app

Start the server with `uv run python main.py`, then run `uv run python scripts/smoke_mcp_app.py --url http://127.0.0.1:8000/mcp`. The script checks tool discovery, the `ui://` HTML resource, structured results, all fifteen sections and the OpenStreetMap link. It reports unavailable sources separately.

To exercise the browser bridge, run `uv run python -m http.server 8014 --bind 127.0.0.1` and open `http://127.0.0.1:8014/tests/fixtures/mcp_app_host.html`. This fixture simulates the host for messages, filters and themes. It is not a ChatGPT runtime test.

For native ChatGPT rendering, [OpenAI's quickstart](https://developers.openai.com/plugins/build/app-quickstart) requires a publicly reachable HTTPS MCP endpoint and an app connection in ChatGPT. A `ui://` URL identifies a resource inside that MCP connection; it does not automatically connect a local server to the ChatGPT account. After connecting, ask ChatGPT to call `mtl_show_dashboard`.

The browser uses `POST /montreal/api` with the same argument validation as the MCP tool. Light and dark themes follow host context, and long cards scroll within their bounds.
