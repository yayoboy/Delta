#!/usr/bin/env python3
"""
Server MCP per l'indicizzazione e l'analisi del codebase.

Questo server espone funzioni che Claude può utilizzare per:
- Elencare i file nel progetto
- Leggere il contenuto dei file
- Accedere all'indice del codebase
"""

import os
import sys
from pathlib import Path
from typing import Optional, List
import hashlib
import mimetypes

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .database import Database


# Inizializza il server MCP
app = Server("codebase-mcp-server")

# Database globale
db: Optional[Database] = None

# Directory del progetto (configurabile)
PROJECT_ROOT = os.environ.get("MCP_PROJECT_ROOT", os.getcwd())


def is_text_file(file_path: str) -> bool:
    """
    Verifica se un file è di tipo testuale.

    Args:
        file_path: Percorso del file

    Returns:
        True se il file è testuale
    """
    # Estensioni comuni di file di testo/codice
    text_extensions = {
        '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
        '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
        '.html', '.css', '.scss', '.sass', '.less',
        '.json', '.yaml', '.yml', '.toml', '.xml', '.ini', '.cfg',
        '.md', '.txt', '.rst', '.tex',
        '.sh', '.bash', '.zsh', '.fish',
        '.sql', '.r', '.m', '.jl',
        '.Dockerfile', '.gitignore', '.env'
    }

    ext = Path(file_path).suffix.lower()
    if ext in text_extensions:
        return True

    # Prova con mimetypes
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type and mime_type.startswith('text/'):
        return True

    return False


def calculate_file_hash(file_path: str) -> str:
    """
    Calcola l'hash SHA256 del contenuto di un file.

    Args:
        file_path: Percorso del file

    Returns:
        Hash SHA256 come stringa esadecimale
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    Elenca gli strumenti disponibili.

    Returns:
        Lista di strumenti MCP
    """
    return [
        Tool(
            name="list_files",
            description="Elenca tutti i file nel progetto, escludendo cartelle nascoste e file binari comuni",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Pattern opzionale per filtrare i file (es. '*.py' per solo file Python)"
                    }
                }
            }
        ),
        Tool(
            name="read_file",
            description="Legge il contenuto di un file specifico",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Percorso relativo del file da leggere"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="get_indexed_files",
            description="Recupera l'elenco di tutti i file indicizzati nel database",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Gestisce le chiamate agli strumenti.

    Args:
        name: Nome dello strumento
        arguments: Argomenti dello strumento

    Returns:
        Lista di contenuti testuali come risposta
    """
    if name == "list_files":
        return await handle_list_files(arguments.get("pattern"))
    elif name == "read_file":
        return await handle_read_file(arguments["path"])
    elif name == "get_indexed_files":
        return await handle_get_indexed_files()
    else:
        raise ValueError(f"Strumento sconosciuto: {name}")


async def handle_list_files(pattern: Optional[str] = None) -> list[TextContent]:
    """
    Gestisce la richiesta di elenco file.

    Args:
        pattern: Pattern opzionale per filtrare i file

    Returns:
        Lista con il contenuto testuale dell'elenco
    """
    files = []
    exclude_dirs = {'.git', '.venv', 'venv', '__pycache__', 'node_modules', '.idea', '.vscode'}

    for root, dirs, filenames in os.walk(PROJECT_ROOT):
        # Rimuovi directory da escludere
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]

        for filename in filenames:
            # Salta file nascosti
            if filename.startswith('.'):
                continue

            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, PROJECT_ROOT)

            # Filtra per pattern se specificato
            if pattern:
                from fnmatch import fnmatch
                if not fnmatch(filename, pattern):
                    continue

            # Include solo file di testo
            if is_text_file(full_path):
                files.append(rel_path)

    files.sort()

    result = f"Trovati {len(files)} file nel progetto:\n\n"
    result += "\n".join(f"- {f}" for f in files)

    return [TextContent(type="text", text=result)]


async def handle_read_file(path: str) -> list[TextContent]:
    """
    Gestisce la richiesta di lettura file.

    Args:
        path: Percorso del file da leggere

    Returns:
        Lista con il contenuto del file
    """
    full_path = os.path.join(PROJECT_ROOT, path)

    # Verifica sicurezza: il file deve essere dentro PROJECT_ROOT
    if not os.path.abspath(full_path).startswith(os.path.abspath(PROJECT_ROOT)):
        return [TextContent(type="text", text=f"Errore: accesso negato a {path}")]

    if not os.path.exists(full_path):
        return [TextContent(type="text", text=f"Errore: file {path} non trovato")]

    if not os.path.isfile(full_path):
        return [TextContent(type="text", text=f"Errore: {path} non è un file")]

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        result = f"Contenuto di {path}:\n\n{content}"
        return [TextContent(type="text", text=result)]

    except UnicodeDecodeError:
        return [TextContent(type="text", text=f"Errore: {path} non è un file di testo")]
    except Exception as e:
        return [TextContent(type="text", text=f"Errore nella lettura di {path}: {str(e)}")]


async def handle_get_indexed_files() -> list[TextContent]:
    """
    Gestisce la richiesta di elenco file indicizzati.

    Returns:
        Lista con l'elenco dei file nel database
    """
    if not db:
        return [TextContent(type="text", text="Errore: database non inizializzato")]

    files = await db.get_all_files()

    if not files:
        return [TextContent(type="text", text="Nessun file indicizzato nel database.")]

    result = f"File indicizzati nel database ({len(files)}):\n\n"
    for file in files:
        result += f"- {file['path']}"
        if file.get('language'):
            result += f" [{file['language']}]"
        if file.get('summary'):
            result += f"\n  Riassunto: {file['summary'][:100]}..."
        result += "\n"

    return [TextContent(type="text", text=result)]


async def main():
    """Avvia il server MCP."""
    global db

    # Inizializza il database
    db = Database()
    await db.connect()

    print(f"Server MCP avviato. Directory progetto: {PROJECT_ROOT}", file=sys.stderr)
    print(f"Database: {db.db_path}", file=sys.stderr)

    try:
        # Avvia il server con comunicazione stdio
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    finally:
        # Chiudi il database alla fine
        await db.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
