"""Tests for BLE MCP tool implementations."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ble_mcp.connection import ConnectionManager
from ble_mcp.tools import (
    tool_connect,
    tool_disconnect,
    tool_enumerate_services,
    tool_monitor_advertisements,
    tool_read_characteristic,
    tool_scan_devices,
    tool_subscribe_notify,
)


@pytest.fixture
def manager():
    """ConnectionManager mock with AsyncMock for all async methods."""
    m = MagicMock(spec=ConnectionManager)
    m.scan = AsyncMock()
    m.monitor_advertisements = AsyncMock()
    m.connect = AsyncMock()
    m.disconnect = AsyncMock()
    m.enumerate_services = AsyncMock()
    m.read_characteristic = AsyncMock()
    m.subscribe_notify = AsyncMock()
    return m


class TestScanDevices:
    @pytest.mark.asyncio
    async def test_returns_devices(self, manager):
        devices = [
            {"name": "Lock", "address": "AA:BB:CC:DD:EE:FF", "rssi": -50},
            {"name": "Sensor", "address": "11:22:33:44:55:66", "rssi": -70},
        ]
        manager.scan.return_value = devices

        result = await tool_scan_devices(manager, duration=5.0)

        manager.scan.assert_awaited_once_with(duration=5.0, name_filter=None)
        assert result["count"] == 2
        assert result["devices"] == devices

    @pytest.mark.asyncio
    async def test_passes_name_filter(self, manager):
        manager.scan.return_value = []

        result = await tool_scan_devices(manager, duration=3.0, name_filter="Lock")

        manager.scan.assert_awaited_once_with(duration=3.0, name_filter="Lock")
        assert result["count"] == 0
        assert result["devices"] == []

    @pytest.mark.asyncio
    async def test_empty_scan(self, manager):
        manager.scan.return_value = []

        result = await tool_scan_devices(manager)

        assert result == {"devices": [], "count": 0}

    @pytest.mark.asyncio
    async def test_scan_error_returns_error_dict(self, manager):
        manager.scan.side_effect = Exception("adapter unavailable")

        result = await tool_scan_devices(manager)

        assert "error" in result
        assert "adapter unavailable" in result["error"]


class TestMonitorAdvertisements:
    @pytest.mark.asyncio
    async def test_returns_records(self, manager):
        records = [
            {"timestamp": "2026-03-25T10:00:00.000Z", "address": "AA:BB:CC:DD:EE:FF", "rssi": -60},
            {"timestamp": "2026-03-25T10:00:01.000Z", "address": "AA:BB:CC:DD:EE:FF", "rssi": -62},
        ]
        manager.monitor_advertisements.return_value = records

        result = await tool_monitor_advertisements(manager, duration=5.0)

        manager.monitor_advertisements.assert_awaited_once_with(
            duration=5.0, device_filter=None
        )
        assert result["count"] == 2
        assert result["advertisements"] == records

    @pytest.mark.asyncio
    async def test_passes_device_filter(self, manager):
        manager.monitor_advertisements.return_value = []

        await tool_monitor_advertisements(
            manager, duration=10.0, device_filter="AA:BB:CC:DD:EE:FF"
        )

        manager.monitor_advertisements.assert_awaited_once_with(
            duration=10.0, device_filter="AA:BB:CC:DD:EE:FF"
        )

    @pytest.mark.asyncio
    async def test_empty_returns_zero_count(self, manager):
        manager.monitor_advertisements.return_value = []

        result = await tool_monitor_advertisements(manager)

        assert result == {"advertisements": [], "count": 0}

    @pytest.mark.asyncio
    async def test_error_returns_error_dict(self, manager):
        manager.monitor_advertisements.side_effect = Exception("no adapter")

        result = await tool_monitor_advertisements(manager)

        assert "error" in result


class TestConnect:
    @pytest.mark.asyncio
    async def test_successful_connect(self, manager):
        manager.connect.return_value = "abc12345"
        manager.get.return_value = {
            "address": "AA:BB:CC:DD:EE:FF",
            "engagement_path": "/engagements/25-03-2026-10-00_BLE_smart-lock",
            "connected": True,
        }

        result = await tool_connect(manager, "AA:BB:CC:DD:EE:FF", "smart-lock")

        manager.connect.assert_awaited_once_with(
            address="AA:BB:CC:DD:EE:FF", engagement_name="smart-lock", project_path=None
        )
        assert result["connection_id"] == "abc12345"
        assert "engagement_path" in result
        assert result["engagement_path"] is not None

    @pytest.mark.asyncio
    async def test_failed_connect_returns_none(self, manager):
        manager.connect.return_value = None

        result = await tool_connect(manager, "AA:BB:CC:DD:EE:FF", "dead-device")

        assert "error" in result
        assert "AA:BB:CC:DD:EE:FF" in result["error"]

    @pytest.mark.asyncio
    async def test_exception_returns_error_dict(self, manager):
        manager.connect.side_effect = Exception("BLE stack crash")

        result = await tool_connect(manager, "AA:BB:CC:DD:EE:FF", "test")

        assert "error" in result
        assert "BLE stack crash" in result["error"]


class TestDisconnect:
    @pytest.mark.asyncio
    async def test_successful_disconnect(self, manager):
        manager.disconnect.return_value = None

        result = await tool_disconnect(manager, "abc12345")

        manager.disconnect.assert_awaited_once_with("abc12345")
        assert result == {"disconnected": True}

    @pytest.mark.asyncio
    async def test_nonexistent_connection_returns_error(self, manager):
        manager.disconnect.side_effect = KeyError("nonexistent")

        result = await tool_disconnect(manager, "nonexistent")

        assert "error" in result
        assert "nonexistent" in result["error"]

    @pytest.mark.asyncio
    async def test_ble_error_returns_error_dict(self, manager):
        manager.disconnect.side_effect = Exception("disconnection failed")

        result = await tool_disconnect(manager, "abc12345")

        assert "error" in result
        assert "disconnection failed" in result["error"]


class TestEnumerateServices:
    @pytest.mark.asyncio
    async def test_returns_services_with_counts(self, manager):
        services = [
            {
                "uuid": "0000180a-0000-1000-8000-00805f9b34fb",
                "name": "Device Information",
                "handle": 1,
                "characteristics": [
                    {"uuid": "00002a29-0000-1000-8000-00805f9b34fb", "name": "Manufacturer Name String"},
                    {"uuid": "00002a26-0000-1000-8000-00805f9b34fb", "name": "Firmware Revision String"},
                ],
            },
            {
                "uuid": "0000180f-0000-1000-8000-00805f9b34fb",
                "name": "Battery Service",
                "handle": 10,
                "characteristics": [
                    {"uuid": "00002a19-0000-1000-8000-00805f9b34fb", "name": "Battery Level"},
                ],
            },
        ]
        manager.enumerate_services.return_value = services

        result = await tool_enumerate_services(manager, "abc12345")

        manager.enumerate_services.assert_awaited_once_with("abc12345")
        assert result["service_count"] == 2
        assert result["characteristic_count"] == 3
        assert result["services"] == services

    @pytest.mark.asyncio
    async def test_nonexistent_connection_returns_error(self, manager):
        manager.enumerate_services.side_effect = KeyError("bad-id")

        result = await tool_enumerate_services(manager, "bad-id")

        assert "error" in result
        assert "bad-id" in result["error"]

    @pytest.mark.asyncio
    async def test_ble_error_returns_error_dict(self, manager):
        manager.enumerate_services.side_effect = Exception("not connected")

        result = await tool_enumerate_services(manager, "abc12345")

        assert "error" in result


class TestReadCharacteristic:
    @pytest.mark.asyncio
    async def test_returns_value(self, manager):
        char_uuid = "00002a29-0000-1000-8000-00805f9b34fb"
        char_result = {
            "uuid": char_uuid,
            "name": "Manufacturer Name String",
            "hex": "546573744d616e756661637475726572",
            "text": "TestManufacturer",
            "bytes": 16,
            "raw": [84, 101, 115, 116],
        }
        manager.read_characteristic.return_value = char_result

        result = await tool_read_characteristic(manager, "abc12345", char_uuid)

        manager.read_characteristic.assert_awaited_once_with("abc12345", char_uuid)
        assert result == char_result

    @pytest.mark.asyncio
    async def test_read_error_returns_error_dict(self, manager):
        manager.read_characteristic.side_effect = Exception("not readable")

        result = await tool_read_characteristic(
            manager, "abc12345", "00002a29-0000-1000-8000-00805f9b34fb"
        )

        assert "error" in result
        assert "not readable" in result["error"]

    @pytest.mark.asyncio
    async def test_nonexistent_connection_returns_error(self, manager):
        manager.read_characteristic.side_effect = KeyError("bad-id")

        result = await tool_read_characteristic(
            manager, "bad-id", "00002a29-0000-1000-8000-00805f9b34fb"
        )

        assert "error" in result
        assert "bad-id" in result["error"]


class TestSubscribeNotify:
    @pytest.mark.asyncio
    async def test_returns_notifications(self, manager):
        char_uuid = "00002a37-0000-1000-8000-00805f9b34fb"
        notifications = [
            {"timestamp": "2026-03-25T10:00:00.000Z", "uuid": char_uuid, "hex": "010203", "bytes": 3},
            {"timestamp": "2026-03-25T10:00:01.000Z", "uuid": char_uuid, "hex": "0405", "bytes": 2},
        ]
        manager.subscribe_notify.return_value = notifications

        result = await tool_subscribe_notify(manager, "abc12345", char_uuid, duration=5.0)

        manager.subscribe_notify.assert_awaited_once_with("abc12345", char_uuid, duration=5.0)
        assert result["count"] == 2
        assert result["notifications"] == notifications
        assert result["uuid"] == char_uuid
        assert result["duration"] == 5.0

    @pytest.mark.asyncio
    async def test_nonexistent_connection_returns_error(self, manager):
        manager.subscribe_notify.side_effect = KeyError("bad-id")

        result = await tool_subscribe_notify(
            manager, "bad-id", "00002a37-0000-1000-8000-00805f9b34fb"
        )

        assert "error" in result
        assert "bad-id" in result["error"]

    @pytest.mark.asyncio
    async def test_ble_error_returns_error_dict(self, manager):
        manager.subscribe_notify.side_effect = Exception("notify not supported")

        result = await tool_subscribe_notify(
            manager, "abc12345", "00002a37-0000-1000-8000-00805f9b34fb"
        )

        assert "error" in result
        assert "notify not supported" in result["error"]

    @pytest.mark.asyncio
    async def test_default_duration(self, manager):
        manager.subscribe_notify.return_value = []

        result = await tool_subscribe_notify(
            manager, "abc12345", "00002a37-0000-1000-8000-00805f9b34fb"
        )

        manager.subscribe_notify.assert_awaited_once_with(
            "abc12345",
            "00002a37-0000-1000-8000-00805f9b34fb",
            duration=30.0,
        )
        assert result["duration"] == 30.0
