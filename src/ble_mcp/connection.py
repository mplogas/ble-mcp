"""BLE connection management -- single owner of all bleak imports.

This module is the ONLY place that imports bleak. Tools call into
ConnectionManager, never bleak directly. Same pattern as hardware.py
in buspirate-mcp and session.py in mitm-mcp.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bleak import BleakClient, BleakScanner

from ble_mcp import gatt_names

log = logging.getLogger(__name__)


def _sanitize_name(name: str) -> str:
    """Strip everything except alphanumerics, hyphens, and underscores."""
    return re.sub(r"[^a-zA-Z0-9_-]", "", name) or "unnamed"


class _Connection:
    """Internal wrapper around a BleakClient and its engagement path."""

    def __init__(
        self,
        conn_id: str,
        client: BleakClient,
        address: str,
        engagement_path: Path,
    ) -> None:
        self.conn_id = conn_id
        self.client = client
        self.address = address
        self.engagement_path = engagement_path


class ConnectionManager:
    """Manages BLE connections and engagement folders.

    All bleak usage is confined to this class. Tools never import bleak.
    """

    def __init__(self, engagements_dir: Path) -> None:
        self._engagements_dir = engagements_dir
        self._connections: dict[str, _Connection] = {}

    async def scan(
        self,
        duration: float,
        name_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Scan for BLE devices. Returns list sorted by RSSI descending."""
        discovered = await BleakScanner.discover(
            timeout=duration, return_adv=True
        )
        results: list[dict[str, Any]] = []
        for device, adv in discovered.values():
            name = adv.local_name or device.name or ""
            if name_filter and name_filter.lower() not in name.lower():
                continue
            mfr_data = {
                str(k): v.hex() for k, v in (adv.manufacturer_data or {}).items()
            }
            results.append({
                "name": name,
                "address": device.address,
                "rssi": adv.rssi,
                "service_uuids": adv.service_uuids or [],
                "manufacturer_data": mfr_data,
                "tx_power": adv.tx_power,
            })
        results.sort(key=lambda d: d["rssi"], reverse=True)
        return results

    async def monitor_advertisements(
        self,
        duration: float,
        device_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Monitor BLE advertisements for a duration, returning timestamped records."""
        records: list[dict[str, Any]] = []

        def _callback(device: Any, adv: Any) -> None:
            if device_filter and device.address != device_filter:
                return
            name = adv.local_name or device.name or ""
            mfr_data = {
                str(k): v.hex() for k, v in (adv.manufacturer_data or {}).items()
            }
            records.append({
                "timestamp": datetime.now(timezone.utc).isoformat(
                    timespec="milliseconds"
                ),
                "name": name,
                "address": device.address,
                "rssi": adv.rssi,
                "service_uuids": adv.service_uuids or [],
                "manufacturer_data": mfr_data,
                "tx_power": adv.tx_power,
            })

        scanner = BleakScanner(detection_callback=_callback)
        await scanner.start()
        try:
            await asyncio.sleep(duration)
        finally:
            await scanner.stop()
        return records

    async def connect(
        self,
        address: str,
        engagement_name: str,
        project_path: str | None = None,
    ) -> str | None:
        """Connect to a BLE device, create engagement folder. Returns conn_id or None."""
        sanitized = _sanitize_name(engagement_name)
        timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M")

        if project_path is not None:
            resolved = Path(project_path).resolve()
            if not resolved.is_relative_to(self._engagements_dir.resolve()):
                raise ValueError("project_path must be under engagements directory")
            engagement_path = resolved / "ble"
        else:
            folder_name = f"{timestamp}_BLE_{sanitized}"
            engagement_path = self._engagements_dir / folder_name
            counter = 1
            while engagement_path.exists():
                folder_name = f"{timestamp}_BLE_{sanitized}-{counter}"
                engagement_path = self._engagements_dir / folder_name
                counter += 1

        client = BleakClient(address, timeout=10.0)
        try:
            await client.connect()
        except Exception:
            log.exception("Failed to connect to %s", address)
            return None

        (engagement_path / "logs").mkdir(parents=True, exist_ok=True)
        (engagement_path / "artifacts").mkdir(parents=True, exist_ok=True)

        conn_id = str(uuid.uuid4())[:8]

        config = {
            "connection_id": conn_id,
            "name": sanitized,
            "address": address,
            "date": timestamp,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        config_path = engagement_path / "config.json"
        config_path.write_text(json.dumps(config, indent=2) + "\n")

        conn = _Connection(
            conn_id=conn_id,
            client=client,
            address=address,
            engagement_path=engagement_path,
        )
        self._connections[conn_id] = conn
        log.info("Connected to %s as %s", address, conn_id)
        return conn_id

    async def disconnect(self, conn_id: str) -> None:
        """Disconnect a BLE device. Raises KeyError if not found."""
        conn = self._connections[conn_id]
        try:
            await conn.client.disconnect()
        finally:
            self._connections.pop(conn_id, None)
        log.info("Disconnected %s", conn_id)

    async def close_all(self) -> None:
        """Disconnect all active BLE connections. Called on shutdown."""
        for conn_id in list(self._connections.keys()):
            try:
                await self.disconnect(conn_id)
            except Exception:
                pass

    def get(self, conn_id: str) -> dict[str, Any] | None:
        """Get connection info. Returns None if not found."""
        conn = self._connections.get(conn_id)
        if conn is None:
            return None
        return {
            "address": conn.address,
            "engagement_path": str(conn.engagement_path),
            "connected": conn.client.is_connected,
        }

    async def enumerate_services(self, conn_id: str) -> list[dict[str, Any]]:
        """Walk GATT services and characteristics. Saves to logs/ble-gatt.json."""
        conn = self._connections[conn_id]
        services_list: list[dict[str, Any]] = []
        for service in conn.client.services:
            chars: list[dict[str, Any]] = []
            for char in service.characteristics:
                descriptors = []
                for desc in char.descriptors:
                    descriptors.append({
                        "uuid": desc.uuid,
                        "handle": desc.handle,
                    })
                chars.append({
                    "uuid": char.uuid,
                    "name": gatt_names.characteristic_name(char.uuid),
                    "properties": char.properties,
                    "handle": char.handle,
                    "descriptors": descriptors,
                })
            services_list.append({
                "uuid": service.uuid,
                "name": gatt_names.service_name(service.uuid),
                "handle": service.handle,
                "characteristics": chars,
            })

        gatt_path = conn.engagement_path / "logs" / "ble-gatt.json"
        gatt_path.write_text(json.dumps(services_list, indent=2) + "\n")
        return services_list

    async def read_characteristic(
        self, conn_id: str, char_uuid: str
    ) -> dict[str, Any]:
        """Read a GATT characteristic. Returns value in multiple formats."""
        conn = self._connections[conn_id]
        data = await conn.client.read_gatt_char(char_uuid)
        raw = list(data)
        try:
            text = data.decode("utf-8")
        except (UnicodeDecodeError, AttributeError):
            text = None
        return {
            "uuid": char_uuid,
            "name": gatt_names.characteristic_name(char_uuid),
            "hex": data.hex(),
            "text": text,
            "bytes": len(data),
            "raw": raw,
        }

    async def subscribe_notify(
        self,
        conn_id: str,
        char_uuid: str,
        duration: float = 30.0,
    ) -> list[dict[str, Any]]:
        """Subscribe to notifications for a duration. Saves to logs/ble-notifications.jsonl."""
        conn = self._connections[conn_id]
        notifications: list[dict[str, Any]] = []

        def _on_notify(_handle: int, data: bytearray) -> None:
            try:
                text = data.decode("utf-8")
            except (UnicodeDecodeError, AttributeError):
                text = None
            notifications.append({
                "timestamp": datetime.now(timezone.utc).isoformat(
                    timespec="milliseconds"
                ),
                "uuid": char_uuid,
                "hex": data.hex(),
                "text": text,
                "bytes": len(data),
                "raw": list(data),
            })

        await conn.client.start_notify(char_uuid, _on_notify)
        try:
            await asyncio.sleep(duration)
        finally:
            await conn.client.stop_notify(char_uuid)

        # Write notifications to JSONL log
        log_path = conn.engagement_path / "logs" / "ble-notifications.jsonl"
        with log_path.open("a") as f:
            for rec in notifications:
                f.write(json.dumps(rec) + "\n")

        return notifications
