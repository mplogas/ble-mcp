"""GATT UUID to human-readable name mapping.

Pure data module -- no BLE dependencies. Maps standard Bluetooth SIG 16-bit UUIDs
to human-readable names for services and characteristics.

Standard BLE base UUID: 0000xxxx-0000-1000-8000-00805f9b34fb
"""

_BLE_BASE_SUFFIX = "-0000-1000-8000-00805f9b34fb"

# Bluetooth SIG assigned service UUIDs (16-bit, lowercase hex)
_SERVICES: dict[str, str] = {
    "1800": "Generic Access",
    "1801": "Generic Attribute",
    "1802": "Immediate Alert",
    "1803": "Link Loss",
    "1804": "Tx Power",
    "1805": "Current Time",
    "1806": "Reference Time Update",
    "1807": "Next DST Change",
    "1808": "Glucose",
    "1809": "Health Thermometer",
    "180a": "Device Information",
    "180b": "Network Availability",
    "180c": "Watchdog",
    "180d": "Heart Rate",
    "180e": "Phone Alert Status",
    "180f": "Battery Service",
    "1810": "Blood Pressure",
    "1811": "Alert Notification",
    "1812": "Human Interface Device",
    "1813": "Scan Parameters",
    "1814": "Running Speed and Cadence",
    "1815": "Automation IO",
    "1816": "Cycling Speed and Cadence",
    "1818": "Cycling Power",
    "1819": "Location and Navigation",
    "181a": "Environmental Sensing",
    "181b": "Body Composition",
    "181c": "User Data",
    "181d": "Weight Scale",
    "181e": "Bond Management",
    "181f": "Continuous Glucose Monitoring",
    "1820": "Internet Protocol Support",
    "1821": "Indoor Positioning",
    "1822": "Pulse Oximeter",
    "1823": "HTTP Proxy",
    "1824": "Transport Discovery",
    "1825": "Object Transfer",
    "1826": "Fitness Machine",
    "1827": "Mesh Provisioning",
    "1828": "Mesh Proxy",
    "1829": "Reconnection Configuration",
}

# Bluetooth SIG assigned characteristic UUIDs (16-bit, lowercase hex)
_CHARACTERISTICS: dict[str, str] = {
    "2a00": "Device Name",
    "2a01": "Appearance",
    "2a02": "Peripheral Privacy Flag",
    "2a03": "Reconnection Address",
    "2a04": "Peripheral Preferred Connection Parameters",
    "2a05": "Service Changed",
    "2a06": "Alert Level",
    "2a07": "Tx Power Level",
    "2a08": "Date Time",
    "2a09": "Day of Week",
    "2a0a": "Day Date Time",
    "2a0c": "Exact Time 256",
    "2a0d": "DST Offset",
    "2a0e": "Time Zone",
    "2a0f": "Local Time Information",
    "2a11": "Time with DST",
    "2a12": "Time Accuracy",
    "2a13": "Time Source",
    "2a14": "Reference Time Information",
    "2a16": "Time Update Control Point",
    "2a17": "Time Update State",
    "2a18": "Glucose Measurement",
    "2a19": "Battery Level",
    "2a1c": "Temperature Measurement",
    "2a1d": "Temperature Type",
    "2a1e": "Intermediate Temperature",
    "2a21": "Measurement Interval",
    "2a22": "Boot Keyboard Input Report",
    "2a23": "System ID",
    "2a24": "Model Number String",
    "2a25": "Serial Number String",
    "2a26": "Firmware Revision String",
    "2a27": "Hardware Revision String",
    "2a28": "Software Revision String",
    "2a29": "Manufacturer Name String",
    "2a2a": "IEEE 11073-20601 Regulatory Certification Data List",
    "2a2b": "Current Time",
    "2a2c": "Magnetic Declination",
    "2a31": "Scan Refresh",
    "2a32": "Boot Keyboard Output Report",
    "2a33": "Boot Mouse Input Report",
    "2a34": "Glucose Measurement Context",
    "2a35": "Blood Pressure Measurement",
    "2a36": "Intermediate Cuff Pressure",
    "2a37": "Heart Rate Measurement",
    "2a38": "Body Sensor Location",
    "2a39": "Heart Rate Control Point",
    "2a3f": "Alert Status",
    "2a40": "Ringer Control Point",
    "2a41": "Ringer Setting",
    "2a42": "Alert Category ID Bit Mask",
    "2a43": "Alert Category ID",
    "2a44": "Alert Notification Control Point",
    "2a45": "Unread Alert Status",
    "2a46": "New Alert",
    "2a47": "Supported New Alert Category",
    "2a48": "Supported Unread Alert Category",
    "2a49": "Blood Pressure Feature",
    "2a4a": "HID Information",
    "2a4b": "Report Map",
    "2a4c": "HID Control Point",
    "2a4d": "Report",
    "2a4e": "Protocol Mode",
    "2a4f": "Scan Interval Window",
    "2a50": "PnP ID",
    "2a51": "Glucose Feature",
    "2a52": "Record Access Control Point",
    "2a53": "RSC Measurement",
    "2a54": "RSC Feature",
    "2a55": "SC Control Point",
    "2a56": "Digital",
    "2a58": "Analog",
    "2a5a": "Aggregate",
    "2a5b": "CSC Measurement",
    "2a5c": "CSC Feature",
    "2a5d": "Sensor Location",
    "2a5e": "PLX Spot-Check Measurement",
    "2a5f": "PLX Continuous Measurement",
    "2a60": "PLX Features",
    "2a63": "Cycling Power Measurement",
    "2a64": "Cycling Power Vector",
    "2a65": "Cycling Power Feature",
    "2a66": "Cycling Power Control Point",
    "2a67": "Location and Speed",
    "2a68": "Navigation",
    "2a69": "Position Quality",
    "2a6a": "LN Feature",
    "2a6b": "LN Control Point",
    "2a6c": "Elevation",
    "2a6d": "Pressure",
    "2a6e": "Temperature",
    "2a6f": "Humidity",
    "2a70": "True Wind Speed",
    "2a71": "True Wind Direction",
    "2a72": "Apparent Wind Speed",
    "2a73": "Apparent Wind Direction",
    "2a74": "Gust Factor",
    "2a75": "Pollen Concentration",
    "2a76": "UV Index",
    "2a77": "Irradiance",
    "2a78": "Rainfall",
    "2a79": "Wind Chill",
    "2a7a": "Heat Index",
    "2a7b": "Dew Point",
}

# Combined lookup for uuid_to_name
_ALL: dict[str, str] = {**_SERVICES, **_CHARACTERISTICS}


def _normalize(uuid_str: str) -> str:
    """Normalize a UUID string to a lowercase 4-character 16-bit hex key.

    Accepts:
    - Short form: "180a", "180A"
    - Full form:  "0000180a-0000-1000-8000-00805f9b34fb"

    Returns the 4-character lowercase hex string, or the original lowercased
    string if it does not match either pattern.
    """
    s = uuid_str.strip().lower()
    if len(s) == 36 and s.endswith(_BLE_BASE_SUFFIX):
        # Full 128-bit BLE base UUID -- extract the 16-bit portion from the
        # first segment's trailing 4 hex digits: "0000xxxx-..."
        first_segment = s.split("-")[0]  # "0000xxxx"
        if len(first_segment) == 8:
            return first_segment[4:]  # last 4 hex chars
    return s


def uuid_to_name(uuid_str: str) -> str:
    """Resolve any UUID (short or full form) to a human-readable name.

    Returns the name if known, otherwise returns the original uuid_str unchanged.
    Lookup is case-insensitive.
    """
    key = _normalize(uuid_str)
    if key in _ALL:
        return _ALL[key]
    return uuid_str


def service_name(uuid_str: str) -> str:
    """Resolve a service UUID to a human-readable name.

    Only resolves UUIDs that are registered as services. Returns uuid_str
    unchanged if unknown or if it is a characteristic UUID.
    """
    key = _normalize(uuid_str)
    if key in _SERVICES:
        return _SERVICES[key]
    return uuid_str


def characteristic_name(uuid_str: str) -> str:
    """Resolve a characteristic UUID to a human-readable name.

    Only resolves UUIDs that are registered as characteristics. Returns uuid_str
    unchanged if unknown or if it is a service UUID.
    """
    key = _normalize(uuid_str)
    if key in _CHARACTERISTICS:
        return _CHARACTERISTICS[key]
    return uuid_str
