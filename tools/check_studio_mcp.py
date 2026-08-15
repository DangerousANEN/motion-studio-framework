"""Smoke-check the local MSF Studio MCP server without opening stdio transport."""
from msf.studio.catalog import search_scenes
from msf.studio.contracts import CapabilityTier
from msf.studio.mcp_server import create_mcp_server


if __name__ == "__main__":
    server = create_mcp_server()
    result = search_scenes("checklist", tier=CapabilityTier.PRESET)
    if not result.items:
        raise SystemExit("catalog discovery returned no stable scenes")
    name = getattr(server, "name", None)
    if not name:
        raise SystemExit("MCP server has no declared name")
    print(f"MCP server: {name}; catalog scene: {result.items[0].name}; OK")
