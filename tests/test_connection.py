"""Tests for BLE connection management."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ble_mcp.connection import ConnectionManager


@pytest.fixture
def manager(engagements_dir):
    return ConnectionManager(engagements_dir)


class TestScanDevices:
    @pytest.mark.asyncio
    async def test_returns_discovered_devices(
        self, manager, mock_ble_device, mock_advertisement_data
    ):
        discover_result = {
            "AA:BB:CC:DD:EE:FF": (mock_ble_device, mock_advertisement_data)
        }
        with patch(
            "ble_mcp.connection.BleakScanner.discover",
            new_callable=AsyncMock,
            return_value=discover_result,
        ):
            results = await manager.scan(duration=5.0)

        assert len(results) == 1
        dev = results[0]
        assert dev["address"] == "AA:BB:CC:DD:EE:FF"
        assert dev["rssi"] == -45
        assert dev["name"] == "TestDevice"
        assert "0000180a-0000-1000-8000-00805f9b34fb" in dev["service_uuids"]
        assert isinstance(dev["manufacturer_data"], dict)
        assert dev["tx_power"] == -10

    @pytest.mark.asyncio
    async def test_name_filter(
        self, manager, mock_ble_device, mock_advertisement_data
    ):
        discover_result = {
            "AA:BB:CC:DD:EE:FF": (mock_ble_device, mock_advertisement_data)
        }
        with patch(
            "ble_mcp.connection.BleakScanner.discover",
            new_callable=AsyncMock,
            return_value=discover_result,
        ):
            # Should match (case-insensitive)
            results = await manager.scan(duration=5.0, name_filter="testdev")
            assert len(results) == 1

            # Should not match
            results = await manager.scan(duration=5.0, name_filter="nonexistent")
            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_empty_scan(self, manager):
        with patch(
            "ble_mcp.connection.BleakScanner.discover",
            new_callable=AsyncMock,
            return_value={},
        ):
            results = await manager.scan(duration=2.0)
        assert results == []


class TestConnect:
    @pytest.mark.asyncio
    async def test_creates_connection_and_engagement_folder(
        self, manager, engagements_dir
    ):
        mock_client = AsyncMock()
        mock_client.is_connected = True
        with patch(
            "ble_mcp.connection.BleakClient", return_value=mock_client
        ):
            conn_id = await manager.connect("AA:BB:CC:DD:EE:FF", "smart-lock")

        assert conn_id is not None
        assert len(conn_id) == 8

        # Engagement folder exists with correct structure
        folders = list(engagements_dir.iterdir())
        assert len(folders) == 1
        eng_folder = folders[0]
        assert (eng_folder / "logs").is_dir()
        assert (eng_folder / "artifacts").is_dir()
        assert (eng_folder / "config.json").exists()

        config = json.loads((eng_folder / "config.json").read_text())
        assert config["connection_id"] == conn_id
        assert config["address"] == "AA:BB:CC:DD:EE:FF"
        assert config["name"] == "smart-lock"

    @pytest.mark.asyncio
    async def test_folder_follows_naming_convention(
        self, manager, engagements_dir
    ):
        mock_client = AsyncMock()
        mock_client.is_connected = True
        with patch(
            "ble_mcp.connection.BleakClient", return_value=mock_client
        ):
            await manager.connect("AA:BB:CC:DD:EE:FF", "smart-lock")

        folders = list(engagements_dir.iterdir())
        folder_name = folders[0].name
        # DD-MM-YYYY-HH-MM_BLE_<name>
        assert "_BLE_" in folder_name
        assert "smart-lock" in folder_name

    @pytest.mark.asyncio
    async def test_name_sanitized(self, manager, engagements_dir):
        mock_client = AsyncMock()
        mock_client.is_connected = True
        with patch(
            "ble_mcp.connection.BleakClient", return_value=mock_client
        ):
            await manager.connect("AA:BB:CC:DD:EE:FF", "my device!@#$%")

        folders = list(engagements_dir.iterdir())
        folder_name = folders[0].name
        assert "mydevice" in folder_name
        # Special chars stripped
        assert "!" not in folder_name
        assert "@" not in folder_name

    @pytest.mark.asyncio
    async def test_connection_failure_returns_none(self, manager, engagements_dir):
        mock_client = AsyncMock()
        mock_client.connect.side_effect = Exception("Connection refused")
        with patch(
            "ble_mcp.connection.BleakClient", return_value=mock_client
        ):
            conn_id = await manager.connect("AA:BB:CC:DD:EE:FF", "dead-device")

        assert conn_id is None
        # No engagement folder created on failure
        assert not engagements_dir.exists() or not list(engagements_dir.iterdir())


class TestDisconnect:
    @pytest.mark.asyncio
    async def test_disconnects_and_removes(self, manager):
        mock_client = AsyncMock()
        mock_client.is_connected = True
        with patch(
            "ble_mcp.connection.BleakClient", return_value=mock_client
        ):
            conn_id = await manager.connect("AA:BB:CC:DD:EE:FF", "test")

        await manager.disconnect(conn_id)
        mock_client.disconnect.assert_awaited_once()
        assert manager.get(conn_id) is None

    @pytest.mark.asyncio
    async def test_nonexistent_raises_keyerror(self, manager):
        with pytest.raises(KeyError):
            await manager.disconnect("nonexistent")


class TestEnumerateServices:
    @pytest.mark.asyncio
    async def test_returns_structured_gatt_map(
        self, manager, engagements_dir, mock_bleak_client
    ):
        with patch(
            "ble_mcp.connection.BleakClient", return_value=mock_bleak_client
        ):
            conn_id = await manager.connect("AA:BB:CC:DD:EE:FF", "gatt-test")

        services = await manager.enumerate_services(conn_id)

        assert len(services) == 1
        svc = services[0]
        assert svc["uuid"] == "0000180a-0000-1000-8000-00805f9b34fb"
        assert svc["name"] == "Device Information"
        assert len(svc["characteristics"]) == 2

        char_names = [c["name"] for c in svc["characteristics"]]
        assert "Manufacturer Name String" in char_names
        assert "Firmware Revision String" in char_names

        # Saved to logs
        gatt_path = engagements_dir / list(engagements_dir.iterdir())[0].name / "logs" / "ble-gatt.json"
        assert gatt_path.exists()
        saved = json.loads(gatt_path.read_text())
        assert len(saved) == 1


class TestReadCharacteristic:
    @pytest.mark.asyncio
    async def test_returns_hex_and_text(self, manager, mock_bleak_client):
        with patch(
            "ble_mcp.connection.BleakClient", return_value=mock_bleak_client
        ):
            conn_id = await manager.connect("AA:BB:CC:DD:EE:FF", "read-test")

        char_uuid = "00002a29-0000-1000-8000-00805f9b34fb"
        result = await manager.read_characteristic(conn_id, char_uuid)

        assert result["uuid"] == char_uuid
        assert result["name"] == "Manufacturer Name String"
        assert result["hex"] == bytearray(b"TestManufacturer").hex()
        assert result["text"] == "TestManufacturer"
        assert result["bytes"] == 16
        assert isinstance(result["raw"], list)

    @pytest.mark.asyncio
    async def test_nonexistent_connection_raises_keyerror(self, manager):
        with pytest.raises(KeyError):
            await manager.read_characteristic("nonexistent", "00002a29-0000-1000-8000-00805f9b34fb")


class TestSubscribeNotify:
    @pytest.mark.asyncio
    async def test_captures_notification_data(
        self, manager, engagements_dir, mock_bleak_client
    ):
        # Make start_notify invoke the callback with sample data
        async def _fake_start_notify(char_uuid, callback):
            callback(0, bytearray(b"\x01\x02\x03"))
            callback(0, bytearray(b"\x04\x05"))

        mock_bleak_client.start_notify = _fake_start_notify
        mock_bleak_client.stop_notify = AsyncMock()

        with patch(
            "ble_mcp.connection.BleakClient", return_value=mock_bleak_client
        ):
            conn_id = await manager.connect("AA:BB:CC:DD:EE:FF", "notify-test")

        with patch("ble_mcp.connection.asyncio.sleep", new_callable=AsyncMock):
            notifications = await manager.subscribe_notify(
                conn_id, "00002a37-0000-1000-8000-00805f9b34fb", duration=1.0
            )

        assert len(notifications) == 2
        assert notifications[0]["hex"] == "010203"
        assert notifications[0]["bytes"] == 3
        assert notifications[1]["hex"] == "0405"
        assert "timestamp" in notifications[0]

        # Check JSONL file written
        eng_folder = list(engagements_dir.iterdir())[0]
        log_path = eng_folder / "logs" / "ble-notifications.jsonl"
        assert log_path.exists()
        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 2
