"""Exercise the Montréal MCP App over Streamable HTTP against a running server."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import timedelta

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import TextResourceContents


async def smoke(url: str, address: str, radius: int) -> dict:
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=90)) as session:
            await session.initialize()
            tool = next(t for t in (await session.list_tools()).tools if t.name == "mtl_show_dashboard")
            assert tool.meta is not None
            uri = tool.meta["ui"]["resourceUri"]
            assert uri.startswith("ui://") and tool.outputSchema
            resource = await session.read_resource(uri)
            content = resource.contents[0]
            assert isinstance(content, TextResourceContents)
            assert content.mimeType == "text/html;profile=mcp-app"
            assert "ui/initialize" in content.text and "ui/notifications/tool-result" in content.text
            result = await session.call_tool(tool.name, {"address": address, "radius_m": radius, "view": "all"})
            assert not result.isError and result.structuredContent
            data = result.structuredContent
            assert len(data["sections"]) == 15
            assert data["openstreetmap_url"].startswith("https://www.openstreetmap.org/")
            return {
                "resource": uri,
                "mime_type": content.mimeType,
                "structured_bytes": len(json.dumps(data, ensure_ascii=False).encode()),
                "sections": {
                    key: {"available": not bool(value.get("error")), "error": value.get("error")}
                    for key, value in data["sections"].items()
                },
                "source": "https://developers.openai.com/plugins/build/app-quickstart",
            }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000/mcp")
    parser.add_argument("--address", default="Hôtel de Ville de Montréal")
    parser.add_argument("--radius", type=int, default=1500)
    args = parser.parse_args()
    print(json.dumps(asyncio.run(smoke(args.url, args.address, args.radius)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
