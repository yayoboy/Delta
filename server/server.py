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
import numpy as np

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from database import Database


# Inizializza il server MCP
app = Server("codebase-mcp-server")

# Database globale
db: Optional[Database] = None

# Linter globale
linter: Optional['CodeLinter'] = None

# Directory del progetto - usa la directory corrente se non specificata
PROJECT_ROOT = os.environ.get("MCP_PROJECT_ROOT")
if not PROJECT_ROOT:
    PROJECT_ROOT = os.getcwd()
    print(f"MCP_PROJECT_ROOT non specificato, uso directory corrente: {PROJECT_ROOT}", file=sys.stderr)


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
        ),
        Tool(
            name="search_symbols",
            description="Cerca simboli (classi, funzioni, metodi) nel codebase per nome",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Nome o pattern del simbolo da cercare"
                    },
                    "kind": {
                        "type": "string",
                        "description": "Tipo di simbolo (opzionale): class, function, method, etc."
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_file_symbols",
            description="Ottiene tutti i simboli (classi, funzioni) definiti in un file specifico",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Percorso relativo del file"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="semantic_search",
            description="Ricerca semantica nel codebase usando gli embedding (trova file simili per contenuto)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Descrizione di cosa cercare (es. 'gestione autenticazione utenti')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Numero massimo di risultati (default: 10)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_symbol_references",
            description="Trova tutte le referenze (chiamate, import) a un simbolo specifico",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol_name": {
                        "type": "string",
                        "description": "Nome del simbolo"
                    }
                },
                "required": ["symbol_name"]
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
    elif name == "search_symbols":
        return await handle_search_symbols(
            arguments["query"],
            arguments.get("kind")
        )
    elif name == "get_file_symbols":
        return await handle_get_file_symbols(arguments["path"])
    elif name == "semantic_search":
        return await handle_semantic_search(
            arguments["query"],
            arguments.get("limit", 10)
        )
    elif name == "get_symbol_references":
        return await handle_get_symbol_references(arguments["symbol_name"])
    else:
        raise ValueError(f"Strumento sconosciuto: {name}")


async def handle_set_project_directory(path: str) -> list[TextContent]:
    """
    Cambia il progetto corrente.

    Args:
        path: Percorso del nuovo progetto

    Returns:
        Conferma del cambiamento
    """
    global PROJECT_ROOT, db, linter

    # Verifica che il path esista
    if not os.path.exists(path):
        return [TextContent(type="text", text=f"Errore: la directory {path} non esiste")]

    if not os.path.isdir(path):
        return [TextContent(type="text", text=f"Errore: {path} non è una directory")]

    # Cambia PROJECT_ROOT
    PROJECT_ROOT = os.path.abspath(path)

    # Reinizializza linter con nuovo progetto
    if LINTERS_AVAILABLE:
        linter = CodeLinter(PROJECT_ROOT)

    result = f"✓ Progetto cambiato: {PROJECT_ROOT}\n\n"

    # Verifica se il progetto è indicizzato
    if db:
        files = await db.get_all_files()
        if files:
            result += f"Database: {len(files)} file indicizzati\n"
            result += f"Database path: {db.db_path}\n\n"
            result += "Puoi iniziare ad analizzare il progetto!"
        else:
            result += "⚠️  Progetto non ancora indicizzato.\n"
            result += f"Esegui: mcp-index index --project {PROJECT_ROOT}"

    return [TextContent(type="text", text=result)]


async def handle_get_current_project() -> list[TextContent]:
    """
    Mostra il progetto corrente.

    Returns:
        Informazioni sul progetto corrente
    """
    result = f"Progetto corrente: {PROJECT_ROOT}\n\n"

    # Info sul database
    if db:
        files = await db.get_all_files()
        result += f"Database: {len(files)} file indicizzati\n"
        result += f"Database path: {db.db_path}\n"

        if files:
            # Statistiche per linguaggio
            languages = {}
            for file in files:
                lang = file.get('language', 'Unknown')
                languages[lang] = languages.get(lang, 0) + 1

            result += f"\nLinguaggi:\n"
            for lang, count in sorted(languages.items(), key=lambda x: -x[1])[:5]:
                result += f"  - {lang}: {count} file\n"

    # Info sui linter disponibili
    if linter:
        tools = linter.get_available_tools()
        if tools:
            result += f"\nLinter disponibili: {', '.join(tools)}"

    return [TextContent(type="text", text=result)]


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


async def handle_search_symbols(query: str, kind: Optional[str] = None) -> list[TextContent]:
    """
    Gestisce la ricerca di simboli per nome.

    Args:
        query: Nome o pattern del simbolo
        kind: Tipo di simbolo opzionale

    Returns:
        Lista con i risultati della ricerca
    """
    if not db:
        return [TextContent(type="text", text="Errore: database non inizializzato")]

    # Usa pattern SQL LIKE
    pattern = f"%{query}%"
    symbols = await db.search_symbols_by_name(pattern)

    # Filtra per kind se specificato
    if kind:
        symbols = [s for s in symbols if s['kind'] == kind]

    if not symbols:
        return [TextContent(type="text", text=f"Nessun simbolo trovato per '{query}'")]

    result = f"Trovati {len(symbols)} simbolo/i per '{query}':\n\n"
    for sym in symbols:
        result += f"**{sym['name']}** ({sym['kind']})\n"
        result += f"  File: {sym['file_path']}:{sym['start_line']}\n"
        if sym.get('signature'):
            result += f"  Firma: {sym['signature']}\n"
        if sym.get('docstring'):
            docstring_preview = sym['docstring'][:100]
            result += f"  Doc: {docstring_preview}...\n"
        result += "\n"

    return [TextContent(type="text", text=result)]


async def handle_get_file_symbols(path: str) -> list[TextContent]:
    """
    Gestisce la richiesta di simboli di un file.

    Args:
        path: Percorso del file

    Returns:
        Lista con i simboli del file
    """
    if not db:
        return [TextContent(type="text", text="Errore: database non inizializzato")]

    # Ottieni file ID
    file_id = await db.get_file_id_by_path(path)

    if not file_id:
        return [TextContent(type="text", text=f"File '{path}' non trovato nel database")]

    # Ottieni simboli
    symbols = await db.get_symbols_by_file(file_id)

    if not symbols:
        return [TextContent(type="text", text=f"Nessun simbolo trovato in '{path}'")]

    result = f"Struttura di {path}:\n\n"

    # Organizza per tipo
    by_kind = {}
    for sym in symbols:
        kind = sym['kind']
        if kind not in by_kind:
            by_kind[kind] = []
        by_kind[kind].append(sym)

    for kind, syms in sorted(by_kind.items()):
        result += f"## {kind.title()}s\n\n"
        for sym in syms:
            indent = "  " if sym.get('parent_id') else ""
            result += f"{indent}- {sym['name']}"
            if sym.get('signature'):
                result += f"{sym['signature']}"
            result += f" (linea {sym['start_line']})\n"
            if sym.get('docstring'):
                doc_preview = sym['docstring'][:80].replace('\n', ' ')
                result += f"{indent}  └─ {doc_preview}...\n"
        result += "\n"

    return [TextContent(type="text", text=result)]


async def handle_semantic_search(query: str, limit: int = 10) -> list[TextContent]:
    """
    Gestisce la ricerca semantica.

    Args:
        query: Query di ricerca
        limit: Numero massimo di risultati

    Returns:
        Lista con i risultati della ricerca
    """
    if not db:
        return [TextContent(type="text", text="Errore: database non inizializzato")]

    try:
        # Importa il modello (lazy loading)
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")
        query_embedding = model.encode(query)

        # Ottieni tutti i file con embedding
        files = await db.get_all_files()
        results = []

        for file in files:
            file_id = file['id']
            emb_data = await db.get_embedding(file_id)

            if emb_data and emb_data.get('embedding'):
                # Deserializza embedding
                file_embedding = np.frombuffer(emb_data['embedding'], dtype=np.float32)

                # Calcola similarità coseno
                similarity = np.dot(query_embedding, file_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(file_embedding)
                )

                results.append({
                    'path': file['path'],
                    'similarity': float(similarity),
                    'summary': file.get('summary', ''),
                    'language': file.get('language', 'N/A')
                })

        # Ordina per similarità
        results.sort(key=lambda x: x['similarity'], reverse=True)
        results = results[:limit]

        if not results:
            return [TextContent(type="text", text="Nessun risultato trovato")]

        result_text = f"Risultati ricerca semantica per '{query}':\n\n"
        for i, res in enumerate(results, 1):
            score = res['similarity'] * 100
            result_text += f"{i}. **{res['path']}** [{res['language']}]\n"
            result_text += f"   Rilevanza: {score:.1f}%\n"
            if res['summary']:
                result_text += f"   {res['summary']}\n"
            result_text += "\n"

        return [TextContent(type="text", text=result_text)]

    except Exception as e:
        return [TextContent(type="text", text=f"Errore nella ricerca semantica: {str(e)}")]


async def handle_get_symbol_references(symbol_name: str) -> list[TextContent]:
    """
    Gestisce la richiesta di referenze a un simbolo.

    Args:
        symbol_name: Nome del simbolo

    Returns:
        Lista con le referenze
    """
    if not db:
        return [TextContent(type="text", text="Errore: database non inizializzato")]

    # Cerca il simbolo
    symbols = await db.search_symbols_by_name(symbol_name)

    if not symbols:
        return [TextContent(type="text", text=f"Simbolo '{symbol_name}' non trovato")]

    result = f"Referenze per '{symbol_name}':\n\n"

    for sym in symbols:
        result += f"**Definizione:** {sym['file_path']}:{sym['start_line']}\n"

        # Ottieni le referenze
        references = await db.get_references_from_symbol(sym['id'])

        if references:
            result += f"\nChiamate/import ({len(references)}):\n"
            for ref in references:
                result += f"  - {ref['to_symbol_name']} ({ref['reference_type']}) alla linea {ref['line']}\n"
        else:
            result += "\nNessuna referenza trovata\n"

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
