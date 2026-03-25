"""BLE MCP server -- stdio transport.

Registers all tools from tools.py with the MCP SDK and runs the
server. Claude Code spawns this process and communicates over stdin/stdout.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from ble_mcp.safety import classify_tool, SafetyTier
from ble_mcp.connection import ConnectionManager
from ble_mcp import tools

logger = logging.getLogger("ble-mcp")

# Engagements dir: env var overrides, fallback to package root.
# In standalone mode: defaults to <repo>/engagements/
# When submoduled: parent repo sets PIDEV_ENGAGEMENTS_DIR via .mcp.json env.
_PACKAGE_ROOT = Path(__file__).resolve().parents[2]
ENGAGEMENTS_DIR = Path(
    os.environ.get("PIDEV_ENGAGEMENTS_DIR", str(_PACKAGE_ROOT / "engagements"))
)

app = Server("ble-mcp")
connection_manager = ConnectionManager(engagements_dir=ENGAGEMENTS_DIR)


TOOL_DEFINITIONS = [
    Tool(
        name="scan_devices",
        description=(
            "Scan for nearby BLE devices and return a list sorted by RSSI. [read-only]"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "duration_s": {
                    "type": "number",
                    "default": 10,
                    "description": "Scan duration in seconds",
                },
                "name_filter": {
                    "type": "string",
                    "description": "Filter results to devices whose name contains this substring",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="monitor_advertisements",
        description=(
            "Monitor BLE advertisements for a fixed duration and return timestamped "
            "records. [read-only]"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "duration_s": {
                    "type": "number",
                    "default": 30,
                    "description": "Monitor duration in seconds",
                },
                "device_filter": {
                    "type": "string",
                    "description": "Filter to a specific device address",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="connect",
        description=(
            "Connect to a BLE device by address and create an engagement folder. "
            "Returns a connection_id for subsequent calls. [allowed-write]"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "BLE device MAC address or UUID (platform-dependent)",
                },
                "engagement_name": {
                    "type": "string",
                    "description": "Target device or engagement name used for the folder",
                },
            },
            "required": ["address", "engagement_name"],
        },
    ),
    Tool(
        name="disconnect",
        description="Disconnect a BLE device by connection ID. [allowed-write]",
        inputSchema={
            "type": "object",
            "properties": {
                "connection_id": {
                    "type": "string",
                    "description": "Connection ID returned by connect",
                },
            },
            "required": ["connection_id"],
        },
    ),
    Tool(
        name="enumerate_services",
        description=(
            "Walk GATT services and characteristics for a connected device. "
            "Saves results to logs/ble-gatt.json. [read-only]"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "connection_id": {
                    "type": "string",
                    "description": "Connection ID returned by connect",
                },
            },
            "required": ["connection_id"],
        },
    ),
    Tool(
        name="read_characteristic",
        description=(
            "Read a single GATT characteristic by UUID. Returns hex, text, and raw "
            "representations. [read-only]"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "connection_id": {
                    "type": "string",
                    "description": "Connection ID returned by connect",
                },
                "characteristic_uuid": {
                    "type": "string",
                    "description": "UUID of the GATT characteristic to read",
                },
            },
            "required": ["connection_id", "characteristic_uuid"],
        },
    ),
    Tool(
        name="subscribe_notify",
        description=(
            "Subscribe to GATT notifications for a characteristic for a fixed duration. "
            "Saves records to logs/ble-notifications.jsonl. [allowed-write]"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "connection_id": {
                    "type": "string",
                    "description": "Connection ID returned by connect",
                },
                "characteristic_uuid": {
                    "type": "string",
                    "description": "UUID of the GATT characteristic to subscribe to",
                },
                "duration_s": {
                    "type": "number",
                    "default": 30,
                    "description": "Duration to collect notifications in seconds",
                },
            },
            "required": ["connection_id", "characteristic_uuid"],
        },
    ),
]


@app.list_tools()
async def list_tools():
    return TOOL_DEFINITIONS


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    tier = classify_tool(name)
    logger.info("tool=%s tier=%s args=%s", name, tier.value, arguments)

    # No approval-write tools in MVP, but keep the gate for future use.
    if tier == SafetyTier.APPROVAL_WRITE:
        if not arguments.get("_confirmed", False):
            desc = f"{name}({', '.join(f'{k}={v}' for k, v in arguments.items())})"
            return [TextContent(
                type="text",
                text=json.dumps({
                    "confirmation_required": True,
                    "tool": name,
                    "arguments": arguments,
                    "message": f"APPROVAL REQUIRED: {desc}. "
                    f"Re-call with _confirmed=true to execute.",
                }),
            )]
        arguments = {k: v for k, v in arguments.items() if k != "_confirmed"}

    try:
        if name == "scan_devices":
            result = await tools.tool_scan_devices(
                manager=connection_manager,
                duration=arguments.get("duration_s", 10),
                name_filter=arguments.get("name_filter"),
            )

        elif name == "monitor_advertisements":
            result = await tools.tool_monitor_advertisements(
                manager=connection_manager,
                duration=arguments.get("duration_s", 30),
                device_filter=arguments.get("device_filter"),
            )

        elif name == "connect":
            result = await tools.tool_connect(
                manager=connection_manager,
                address=arguments["address"],
                engagement_name=arguments["engagement_name"],
            )

        elif name == "disconnect":
            result = await tools.tool_disconnect(
                manager=connection_manager,
                connection_id=arguments["connection_id"],
            )

        elif name == "enumerate_services":
            result = await tools.tool_enumerate_services(
                manager=connection_manager,
                connection_id=arguments["connection_id"],
            )

        elif name == "read_characteristic":
            result = await tools.tool_read_characteristic(
                manager=connection_manager,
                connection_id=arguments["connection_id"],
                characteristic_uuid=arguments["characteristic_uuid"],
            )

        elif name == "subscribe_notify":
            result = await tools.tool_subscribe_notify(
                manager=connection_manager,
                connection_id=arguments["connection_id"],
                characteristic_uuid=arguments["characteristic_uuid"],
                duration=arguments.get("duration_s", 30),
            )

        else:
            result = {"error": f"Unknown tool: {name}"}

    except Exception as exc:
        logger.error("tool=%s error=%s", name, exc)
        result = {"error": str(exc), "tool": name}

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
