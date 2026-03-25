"""Shared test fixtures for ble-mcp tests."""

import pytest
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture
def engagements_dir(tmp_path):
    """Temporary engagements directory for tests."""
    return tmp_path / "engagements"


@pytest.fixture
def mock_ble_device():
    """Mock bleak BLEDevice."""
    device = MagicMock()
    device.name = "TestDevice"
    device.address = "AA:BB:CC:DD:EE:FF"
    return device


@pytest.fixture
def mock_advertisement_data():
    """Mock bleak AdvertisementData."""
    adv = MagicMock()
    adv.local_name = "TestDevice"
    adv.rssi = -45
    adv.service_uuids = ["0000180a-0000-1000-8000-00805f9b34fb"]
    adv.manufacturer_data = {0x004C: b"\x02\x15\x01\x02\x03"}
    adv.service_data = {}
    adv.tx_power = -10
    return adv


@pytest.fixture
def mock_gatt_service():
    """Mock bleak BleakGATTService."""
    service = MagicMock()
    service.uuid = "0000180a-0000-1000-8000-00805f9b34fb"
    service.description = "Device Information"
    service.handle = 1

    char1 = MagicMock()
    char1.uuid = "00002a29-0000-1000-8000-00805f9b34fb"
    char1.description = "Manufacturer Name String"
    char1.properties = ["read"]
    char1.handle = 2
    char1.descriptors = []

    char2 = MagicMock()
    char2.uuid = "00002a26-0000-1000-8000-00805f9b34fb"
    char2.description = "Firmware Revision String"
    char2.properties = ["read"]
    char2.handle = 3
    char2.descriptors = []

    service.characteristics = [char1, char2]
    return service


@pytest.fixture
def mock_bleak_client(mock_gatt_service):
    """Mock BleakClient with async methods."""
    client = AsyncMock()
    client.is_connected = True
    client.address = "AA:BB:CC:DD:EE:FF"
    client.services = MagicMock()
    client.services.__iter__ = MagicMock(return_value=iter([mock_gatt_service]))
    client.read_gatt_char = AsyncMock(return_value=bytearray(b"TestManufacturer"))
    return client
