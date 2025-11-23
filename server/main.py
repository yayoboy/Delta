#!/usr/bin/env python3
"""
Entry point per l'estensione Claude Desktop.

Avvia il server MCP per l'analisi del codebase.
"""

import asyncio
import sys
import os

# Aggiungi la directory corrente al path per gli import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import main

if __name__ == "__main__":
    asyncio.run(main())
