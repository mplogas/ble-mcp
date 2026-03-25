# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project

ble-mcp is an MCP server that orchestrates Bluetooth Low Energy scanning and GATT
enumeration for IoT security testing, exposing scan and inspection operations as
MCP tools over stdio transport.

## Architecture

    MCP client (Claude Code, etc.)
      |
      stdio transport
      |
    ble-mcp (server.py)
      |
      tools.py -> connection.py -> bleak (BleakScanner, BleakClient)
      |
    Bluetooth adapter (hci0)

connection.py is the ONLY module that owns BleakClient instances. Everything else
talks to connection.py. This prevents race conditions from split connection
ownership.

## Safety Model

Three tiers enforced at the MCP server boundary:

- **read-only**: full autonomy (list_adapters, scan_devices, get_scan_results)
- **allowed-write**: autonomous but logged (connect_device, disconnect_device, enumerate_gatt, read_characteristic)
- **approval-write**: reserved for write/notify operations that modify device state (write_characteristic, subscribe_notify)

Reading characteristics is non-destructive. Writing or subscribing can trigger
firmware behavior. The approval gate is there because an IoT device might act on
an unexpected write.

## Build and Run

    # Install
    pip install -e ".[dev]"

    # Run server (stdio transport, spawned by MCP client)
    python -m ble_mcp

    # Tests (no Bluetooth hardware needed)
    pytest

    # Integration tests (Bluetooth adapter required)
    pytest tests/ -m bluetooth

## Prerequisites

- bleak installed (pulled in by package dependencies)
- Bluetooth adapter present and accessible (hci0 or equivalent)
- User must be in the `bluetooth` group or running as root for raw adapter access
- On Linux, BlueZ must be running: systemctl status bluetooth

## Style

- Python 3.11+
- No emojis, no em-dashes in code, comments, commits, or docs
- Commit messages: short, to the point
