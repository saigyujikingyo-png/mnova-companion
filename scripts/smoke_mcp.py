"""Exercise a real stdio subprocess; no native application is started."""

import asyncio
import json
import os
import sys
import tempfile

from jsonschema import Draft202012Validator
from mcp import Client
from mcp.client.stdio import StdioServerParameters


async def main():
    with tempfile.TemporaryDirectory(prefix="mnova-mcp-") as temporary:
        async with Client(
            StdioServerParameters(
                command=sys.executable,
                args=["-m", "mnova_companion"],
                env={
                    **os.environ,
                    "MNOVA_COMPANION_HOME": temporary,
                    "MNOVA_ALLOWED_INPUT_ROOTS": "[]",
                },
            )
        ) as client:
            tools = await client.list_tools()
            schemas = {tool.name: tool.output_schema for tool in tools.tools}
            assert len(schemas) == 6
            cases = {
                "mnova_status": {},
                "mnova_help": {"operation": "mnova_status"},
                "mnova_open": {"source": temporary},
                "mnova_run": {"operation": "process_1d", "idempotency_key": "smoke-no-write"},
                "mnova_job": {"job_id": "0" * 32},
                "mnova_artifacts": {},
            }
            for name, arguments in cases.items():
                result = await client.call_tool(name, arguments)
                payload = result.structured_content
                Draft202012Validator(schemas[name]).validate(payload)
                assert json.loads(result.content[0].text) == payload
                assert result.is_error == (payload["error"] is not None)
            invalid = await client.call_tool("mnova_status", {"unknown": "field"})
            assert invalid.is_error
            assert invalid.structured_content["error"]["code"] == "INVALID_ARGUMENT"
    print("PASS: actual MCP stdio subprocess, 6 tools, structured/text parity and error branches.")
    print("Scope: protocol only; not a native or host-model acceptance test.")


if __name__ == "__main__":
    asyncio.run(main())
