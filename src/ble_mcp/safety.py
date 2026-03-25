"""Three-tier safety model for BLE MCP tools.

Tiers:
  read-only       -- full autonomy, no side effects
  allowed-write   -- autonomous, all calls logged
  approval-write  -- blocks until human confirms (no MVP tools)
"""

from __future__ import annotations

from enum import Enum


class SafetyTier(Enum):
    READ_ONLY = "read-only"
    ALLOWED_WRITE = "allowed-write"
    APPROVAL_WRITE = "approval-write"


_TOOL_TIERS: dict[str, SafetyTier] = {
    "scan_devices": SafetyTier.READ_ONLY,
    "monitor_advertisements": SafetyTier.READ_ONLY,
    "enumerate_services": SafetyTier.READ_ONLY,
    "read_characteristic": SafetyTier.READ_ONLY,
    "connect": SafetyTier.ALLOWED_WRITE,
    "disconnect": SafetyTier.ALLOWED_WRITE,
    "subscribe_notify": SafetyTier.ALLOWED_WRITE,
}


def classify_tool(tool_name: str) -> SafetyTier:
    """Return the safety tier for a tool name."""
    tier = _TOOL_TIERS.get(tool_name)
    if tier is None:
        raise ValueError(f"Unknown tool: {tool_name}")
    return tier
