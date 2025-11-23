"""
Entry point per eseguire il modulo come script.

Permette di eseguire: python -m mcp_server
"""

from server import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
