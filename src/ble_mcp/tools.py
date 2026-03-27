"""BLE MCP tool implementations.

All tools are async functions that delegate to ConnectionManager. No bleak
imports here -- that boundary is enforced in connection.py.
"""

from __future__ import annotations

from typing import Any

from ble_mcp.connection import ConnectionManager


async def tool_scan_devices(
    manager: ConnectionManager,
    duration: float = 10.0,
    name_filter: str | None = None,
) -> dict[str, Any]:
    """Scan for BLE devices and return a summary."""
    try:
        devices = await manager.scan(duration=duration, name_filter=name_filter)
    except Exception as exc:
        return {"error": str(exc)}
    return {"devices": devices, "count": len(devices)}


async def tool_monitor_advertisements(
    manager: ConnectionManager,
    duration: float = 30.0,
    device_filter: str | None = None,
) -> dict[str, Any]:
    """Monitor BLE advertisements for a fixed duration."""
    try:
        advertisements = await manager.monitor_advertisements(
            duration=duration, device_filter=device_filter
        )
    except Exception as exc:
        return {"error": str(exc)}
    return {"advertisements": advertisements, "count": len(advertisements)}


async def tool_connect(
    manager: ConnectionManager,
    address: str,
    engagement_name: str,
    project_path: str | None = None,
) -> dict[str, Any]:
    """Connect to a BLE device and create an engagement folder."""
    try:
        conn_id = await manager.connect(address=address, engagement_name=engagement_name, project_path=project_path)
    except Exception as exc:
        return {"error": str(exc)}
    if conn_id is None:
        return {"error": f"Failed to connect to {address}"}
    info = manager.get(conn_id)
    return {
        "connection_id": conn_id,
        "engagement_path": info["engagement_path"] if info else None,
    }


async def tool_disconnect(
    manager: ConnectionManager,
    connection_id: str,
) -> dict[str, Any]:
    """Disconnect a BLE device by connection ID."""
    try:
        await manager.disconnect(connection_id)
    except KeyError:
        return {"error": f"No connection with id {connection_id!r}"}
    except Exception as exc:
        return {"error": str(exc)}
    return {"disconnected": True}


async def tool_enumerate_services(
    manager: ConnectionManager,
    connection_id: str,
) -> dict[str, Any]:
    """Walk GATT services and characteristics for a connected device."""
    try:
        services = await manager.enumerate_services(connection_id)
    except KeyError:
        return {"error": f"No connection with id {connection_id!r}"}
    except Exception as exc:
        return {"error": str(exc)}
    characteristic_count = sum(len(svc["characteristics"]) for svc in services)
    return {
        "services": services,
        "service_count": len(services),
        "characteristic_count": characteristic_count,
    }


async def tool_read_characteristic(
    manager: ConnectionManager,
    connection_id: str,
    characteristic_uuid: str,
) -> dict[str, Any]:
    """Read a single GATT characteristic by UUID."""
    try:
        result = await manager.read_characteristic(connection_id, characteristic_uuid)
    except KeyError:
        return {"error": f"No connection with id {connection_id!r}"}
    except Exception as exc:
        return {"error": str(exc)}
    return result


async def tool_subscribe_notify(
    manager: ConnectionManager,
    connection_id: str,
    characteristic_uuid: str,
    duration: float = 30.0,
) -> dict[str, Any]:
    """Subscribe to GATT notifications for a duration."""
    try:
        notifications = await manager.subscribe_notify(
            connection_id, characteristic_uuid, duration=duration
        )
    except KeyError:
        return {"error": f"No connection with id {connection_id!r}"}
    except Exception as exc:
        return {"error": str(exc)}
    return {
        "notifications": notifications,
        "count": len(notifications),
        "uuid": characteristic_uuid,
        "duration": duration,
    }
