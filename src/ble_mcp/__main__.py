"""Allow running as: python -m ble_mcp"""

from ble_mcp.server import main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
