"""Dispatch tests for ble-mcp.

Verifies that server.py call_tool correctly routes every tool name to the
corresponding tools.tool_* function without TypeError or missing arguments.
Tool functions are patched to AsyncMock so this tests ONLY the dispatch
routing and argument unpacking, not tool logic.
"""

import json

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from mcp.types import TextContent

from ble_mcp import server, tools

TOOL_ARGS = {
    "scan_devices": {},
    "monitor_advertisements": {},
    "connect": {"address": "AA:BB:CC:DD:EE:FF", "engagement_name": "test"},
    "disconnect": {"connection_id": "t"},
    "enumerate_services": {"connection_id": "t"},
    "read_characteristic": {
        "connection_id": "t",
        "characteristic_uuid": "0000180a-0000-1000-8000-00805f9b34fb",
    },
    "subscribe_notify": {
        "connection_id": "t",
        "characteristic_uuid": "0000ffe1-0000-1000-8000-00805f9b34fb",
    },
}


@pytest.fixture(autouse=True)
def _mock_globals():
    """Patch module-level globals and all tool functions."""
    patches = [
        patch.object(server, "connection_manager", MagicMock()),
    ]
    for name in dir(tools):
        if name.startswith("tool_"):
            patches.append(
                patch.object(
                    tools, name, new_callable=AsyncMock, return_value={"ok": True}
                )
            )
    for p in patches:
        p.start()
    yield
    patch.stopall()


@pytest.mark.asyncio
@pytest.mark.parametrize("tool_name,args", TOOL_ARGS.items())
async def test_dispatch(tool_name, args):
    """call_tool should route {tool_name} without crashing."""
    result = await server.call_tool(tool_name, args)
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    data = json.loads(result[0].text)
    assert "Unknown tool" not in data.get("error", "")


async def test_unknown_tool():
    """Unknown tool names raise ValueError from classify_tool."""
    with pytest.raises(ValueError, match="Unknown tool"):
        await server.call_tool("nonexistent_tool", {})
