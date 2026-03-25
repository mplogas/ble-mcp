# ble-mcp

MCP server for Bluetooth Low Energy scanning and GATT enumeration in IoT security testing. Uses [bleak](https://github.com/hbldh/bleak) to discover devices, inspect their GATT profiles, read characteristics, and capture notification streams. Exposes operations as [Model Context Protocol](https://modelcontextprotocol.io/) tools over stdio transport.

Built for use with Claude Code on a Raspberry Pi 5, but works with any MCP client on any platform with a Bluetooth adapter.

## What it does

- **BLE scanning:** discover nearby devices with name, MAC, RSSI, advertised services, manufacturer data
- **Advertisement monitoring:** passive capture of BLE advertisement payloads over time
- **GATT enumeration:** map services, characteristics, and descriptors with human-readable names
- **Characteristic reading:** read values with hex, text, and raw representations
- **Notification capture:** subscribe to characteristic notifications and log timestamped data
- **Engagement logging:** per-engagement folders with GATT maps, notification logs, and config

## Requirements

- Python 3.11+
- BlueZ (system Bluetooth stack, pre-installed on Raspberry Pi OS)
- Bluetooth adapter must be unblocked: `rfkill unblock bluetooth`

## Install

```bash
git clone https://github.com/mplogas/ble-mcp.git
cd ble-mcp
pip install -e ".[dev]"
```

## MCP Client Configuration

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "ble": {
      "command": "/path/to/.venv/bin/python",
      "args": ["-m", "ble_mcp"],
      "env": {
        "PIDEV_ENGAGEMENTS_DIR": "/path/to/engagements"
      }
    }
  }
}
```

Set `PIDEV_ENGAGEMENTS_DIR` to control where engagement logs are written. Defaults to `./engagements/` relative to the package root.

## Tools

| Tool | Safety Tier | Description |
|---|---|---|
| `scan_devices` | read-only | Discover nearby BLE devices |
| `monitor_advertisements` | read-only | Passively capture advertisement data |
| `enumerate_services` | read-only | List GATT services and characteristics |
| `read_characteristic` | read-only | Read a characteristic value by UUID |
| `connect` | allowed-write | Connect to a device, create engagement folder |
| `disconnect` | allowed-write | Disconnect and finalize logs |
| `subscribe_notify` | allowed-write | Subscribe to notifications (writes CCCD on device) |

## Safety Model

Three tiers enforced at the MCP server boundary:

- **read-only:** full autonomy, scanning and reading cannot damage hardware
- **allowed-write:** autonomous, all calls logged. `connect` occupies the device's BLE slot, `subscribe_notify` writes the CCCD descriptor to enable notifications
- **approval-write:** reserved for future write/pair operations (no MVP tools)

## Architecture

```
ble-mcp (server.py)
  |
  tools.py -> connection.py -> bleak (BleakClient, BleakScanner)
  |
BlueZ / D-Bus
  |
Pi 5 onboard Bluetooth
```

- `connection.py` is the only module that imports bleak. Tools call into connection.py, never create BLE clients directly.
- No subprocesses needed (unlike mitm-mcp). All BLE operations happen in-process via bleak's async API.
- Standard Bluetooth SIG UUIDs are resolved to human-readable names via `gatt_names.py`.

## Known Constraints

- **Single connection:** the Pi's onboard Bluetooth can maintain one or a small number of concurrent BLE connections. The MVP supports one at a time.
- **Range:** BLE range is ~10m indoors. Target must be physically close.
- **Device sleep:** battery-powered BLE devices may disconnect after a timeout if idle. Keep the device active during enumeration.
- **Scanning during connection:** some adapters cannot scan while maintaining a connection.

## Tests

```bash
pytest              # 65 tests, no Bluetooth hardware needed
pytest -m bluetooth # integration tests, Bluetooth adapter required
```

## License

MIT
