"""End-to-end stdio protocol check for the local MSF Studio MCP server."""
from __future__ import annotations

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from msf.studio.catalog import all_scenes


EXPANSION_SCENES = {scene.name for scene in all_scenes()}
EXPANSION_STYLES = {
    "aurora_flux", "cobalt_command", "infrared_alert", "violet_luxe", "porcelain",
    "liquid_chrome", "kinetic_poster", "midnight_orbit", "pixel_arcade", "coral_creator",
}


def tool_text(result: object) -> str:
    content = getattr(result, "content", [])
    return "\n".join(item.text for item in content if hasattr(item, "text"))


async def main() -> None:
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = {**os.environ, "PYTHONPATH": repo}
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "msf.studio.mcp_server"],
        env=env,
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            required = {"search_scene_catalog", "describe_scene", "list_style_families", "validate_research_evidence", "research_topic_to_storyboard", "validate_storyboard", "inspect_run"}
            missing = required - names
            if missing:
                raise RuntimeError(f"MCP tools missing: {sorted(missing)}")
            result = await session.call_tool("search_scene_catalog", arguments={"tier": "preset", "limit": 100})
            text = tool_text(result)
            required_catalog = {"AgentRunConsole", "AssetOrbit3D", "BenchmarkArena", "DataCube", "DecisionGrid"}
            missing_catalog = sorted(name for name in required_catalog if name not in text)
            if missing_catalog:
                raise RuntimeError(f"Live MCP catalog page missing representative expansion scenes: {missing_catalog}")
            for name in sorted(EXPANSION_SCENES):
                manifest = await session.call_tool("describe_scene", arguments={"name": name, "tier": "preset"})
                manifest_text = tool_text(manifest)
                if name not in manifest_text:
                    raise RuntimeError(f"MCP describe_scene unavailable for expansion preset: {name}")
            styles = await session.call_tool("list_style_families", arguments={})
            style_text = tool_text(styles)
            if "product_tutorial" not in style_text or "llm_hubs_neon" not in style_text:
                raise RuntimeError("Live MCP style catalog did not include required visual families")
            missing_styles = sorted(name for name in EXPANSION_STYLES if name not in style_text)
            if missing_styles:
                raise RuntimeError(f"Live MCP style catalog missing expansion families: {missing_styles}")
            print(f"protocol_tools={len(names)} scenes={len(EXPANSION_SCENES)} manifests={len(EXPANSION_SCENES)} styles=+10")


if __name__ == "__main__":
    asyncio.run(main())
