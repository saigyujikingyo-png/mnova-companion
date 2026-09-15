"""MCP stdio transport for the same typed service used by local acceptance."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.shared.exceptions import MCPError
from mcp_types import ErrorData, ListToolsResult, Tool, ToolAnnotations

from . import __version__
from .contracts import INPUTS, OUTPUTS
from .service import DESCRIPTIONS, Service


def create_server(service: Service) -> Server:
    async def list_tools(context, params):
        return ListToolsResult(
            tools=[
                Tool(
                    name=name,
                    description=DESCRIPTIONS[name],
                    inputSchema=model.model_json_schema(),
                    outputSchema=OUTPUTS[name].model_json_schema(),
                    annotations=ToolAnnotations(
                        readOnlyHint=name in {"mnova_status", "mnova_help"},
                        destructiveHint=False,
                        openWorldHint=False,
                    ),
                )
                for name, model in INPUTS.items()
            ]
        )

    async def call_tool(context, params):
        if params.name not in INPUTS:
            raise MCPError(ErrorData(code=-32601, message="Unknown Mnova Companion tool"))
        return await asyncio.to_thread(service.call, params.name, params.arguments or {})

    return Server(
        "mnova-companion",
        version=__version__,
        on_list_tools=list_tools,
        on_call_tool=call_tool,
        instructions=(
            "Development preview. Start with mnova_status. Native scientific operations remain "
            "gated unless the returned capability is implemented and verified. Staged inputs "
            "are not imported Mnova documents. File bytes and receiving-host acceptance differ."
        ),
    )


async def serve():
    default = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local/share")) / "MnovaCompanion"
    root = Path(os.environ.get("MNOVA_COMPANION_HOME", str(default)))
    allowed = json.loads(os.environ.get("MNOVA_ALLOWED_INPUT_ROOTS", "[]"))
    if not isinstance(allowed, list) or not all(isinstance(item, str) for item in allowed):
        raise ValueError("MNOVA_ALLOWED_INPUT_ROOTS must be an array of selected directory paths")
    server = create_server(Service(root, allowed_input_roots=[Path(item) for item in allowed]))
    async with stdio_server() as (reader, writer):
        await server.run(reader, writer, server.create_initialization_options())


def main():
    asyncio.run(serve())


if __name__ == "__main__":
    main()
