"""Tests for gatt_names module -- UUID to human-readable name mapping."""

import pytest
from ble_mcp.gatt_names import uuid_to_name, service_name, characteristic_name


BLE_BASE_SUFFIX = "-0000-1000-8000-00805f9b34fb"


class TestUuidToName:
    def test_known_service_short_form(self):
        assert uuid_to_name("180a") == "Device Information"

    def test_known_service_full_form(self):
        assert uuid_to_name("0000180a-0000-1000-8000-00805f9b34fb") == "Device Information"

    def test_known_characteristic_short_form(self):
        assert uuid_to_name("2a29") == "Manufacturer Name String"

    def test_known_characteristic_full_form(self):
        assert uuid_to_name("00002a29-0000-1000-8000-00805f9b34fb") == "Manufacturer Name String"

    def test_unknown_uuid_returned_as_is(self):
        unknown = "deadbeef-0000-1000-8000-00805f9b34fb"
        assert uuid_to_name(unknown) == unknown

    def test_unknown_short_uuid_returned_as_is(self):
        assert uuid_to_name("ffff") == "ffff"

    def test_case_insensitive_upper(self):
        assert uuid_to_name("180A") == "Device Information"

    def test_case_insensitive_mixed(self):
        assert uuid_to_name("0000180A-0000-1000-8000-00805F9B34FB") == "Device Information"

    def test_case_insensitive_characteristic(self):
        assert uuid_to_name("2A29") == "Manufacturer Name String"

    def test_all_required_services(self):
        services = {
            "1800": "Generic Access",
            "1801": "Generic Attribute",
            "180a": "Device Information",
            "180d": "Heart Rate",
            "180f": "Battery Service",
            "181a": "Environmental Sensing",
        }
        for short, name in services.items():
            assert uuid_to_name(short) == name, f"UUID {short} expected '{name}'"

    def test_all_required_characteristics(self):
        chars = {
            "2a00": "Device Name",
            "2a19": "Battery Level",
            "2a24": "Model Number String",
            "2a25": "Serial Number String",
            "2a26": "Firmware Revision String",
            "2a27": "Hardware Revision String",
            "2a28": "Software Revision String",
            "2a29": "Manufacturer Name String",
            "2a6e": "Temperature",
            "2a6f": "Humidity",
        }
        for short, name in chars.items():
            assert uuid_to_name(short) == name, f"UUID {short} expected '{name}'"


class TestServiceName:
    def test_known_service_short(self):
        assert service_name("180a") == "Device Information"

    def test_known_service_full(self):
        assert service_name("0000180a-0000-1000-8000-00805f9b34fb") == "Device Information"

    def test_characteristic_uuid_returns_as_is_from_service_lookup(self):
        # 2a29 is a characteristic, not a service -- service_name should not resolve it
        assert service_name("2a29") == "2a29"

    def test_unknown_returns_as_is(self):
        assert service_name("ffff") == "ffff"

    def test_case_insensitive(self):
        assert service_name("180A") == "Device Information"


class TestCharacteristicName:
    def test_known_characteristic_short(self):
        assert characteristic_name("2a29") == "Manufacturer Name String"

    def test_known_characteristic_full(self):
        assert characteristic_name("00002a29-0000-1000-8000-00805f9b34fb") == "Manufacturer Name String"

    def test_service_uuid_returns_as_is_from_characteristic_lookup(self):
        # 180a is a service, not a characteristic
        assert characteristic_name("180a") == "180a"

    def test_unknown_returns_as_is(self):
        assert characteristic_name("ffff") == "ffff"

    def test_case_insensitive(self):
        assert characteristic_name("2A29") == "Manufacturer Name String"

    def test_battery_level(self):
        assert characteristic_name("2a19") == "Battery Level"

    def test_temperature(self):
        assert characteristic_name("2a6e") == "Temperature"

    def test_humidity(self):
        assert characteristic_name("2a6f") == "Humidity"
