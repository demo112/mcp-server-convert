"""Entry point for mcp-server-convert."""

from .server import main

import asyncio
asyncio.run(main())
