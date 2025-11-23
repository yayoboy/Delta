#!/usr/bin/env python3
"""
CLI per gestire l'indicizzazione del codebase.
"""

import asyncio
import argparse
import os
import sys

from database import Database
from indexer import CodebaseIndexer


async def cmd_index(args):
    """Comando: indicizza il progetto."""
    project_root = args.project or os.environ.get("MCP_PROJECT_ROOT", os.getcwd())

    print(f"Indicizzazione progetto: {project_root}")

    db = Database(args.db)
    await db.connect()

    try:
        indexer = CodebaseIndexer(project_root, db)
        stats = await indexer.index_all(force=args.force)

        print(f"\nStatistiche:")
        print(f"  Indicizzati: {stats['indexed']}")
        print(f"  Saltati: {stats['skipped']}")
        print(f"  Totale: {stats['total']}")

    finally:
        await db.close()


async def cmd_stats(args):
    """Comando: mostra statistiche del database."""
    db = Database(args.db)
    await db.connect()

    try:
        files = await db.get_all_files()

        print(f"\nStatistiche Database:")
        print(f"  Totale file: {len(files)}")

        # Conta per linguaggio
        languages = {}
        for file in files:
            lang = file.get('language') or 'Sconosciuto'
            languages[lang] = languages.get(lang, 0) + 1

        print(f"\nFile per linguaggio:")
        for lang, count in sorted(languages.items(), key=lambda x: -x[1]):
            print(f"  {lang}: {count}")

        # Dimensione totale
        total_size = sum(file.get('file_size', 0) for file in files)
        print(f"\nDimensione totale: {total_size / 1024:.2f} KB")

    finally:
        await db.close()


async def cmd_list(args):
    """Comando: elenca i file indicizzati."""
    db = Database(args.db)
    await db.connect()

    try:
        files = await db.get_all_files()

        if args.language:
            files = [f for f in files if f.get('language') == args.language]

        print(f"\nFile indicizzati ({len(files)}):\n")

        for file in files:
            lang = file.get('language', 'N/A')
            print(f"  [{lang:12}] {file['path']}")
            if args.verbose and file.get('summary'):
                print(f"    └─ {file['summary'][:80]}...")

    finally:
        await db.close()


def main():
    """Entry point principale della CLI."""
    parser = argparse.ArgumentParser(
        description="Gestione dell'indicizzazione del codebase MCP"
    )

    parser.add_argument(
        '--db',
        default='mcp_data/codebase.db',
        help='Percorso del database SQLite (default: mcp_data/codebase.db)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Comandi disponibili')

    # Comando: index
    parser_index = subparsers.add_parser('index', help='Indicizza il progetto')
    parser_index.add_argument(
        '--project',
        help='Percorso del progetto (default: MCP_PROJECT_ROOT o cwd)'
    )
    parser_index.add_argument(
        '--force',
        action='store_true',
        help='Forza re-indicizzazione di tutti i file'
    )
    parser_index.set_defaults(func=cmd_index)

    # Comando: stats
    parser_stats = subparsers.add_parser('stats', help='Mostra statistiche')
    parser_stats.set_defaults(func=cmd_stats)

    # Comando: list
    parser_list = subparsers.add_parser('list', help='Elenca file indicizzati')
    parser_list.add_argument(
        '--language',
        help='Filtra per linguaggio'
    )
    parser_list.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Mostra riassunti'
    )
    parser_list.set_defaults(func=cmd_list)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Esegui il comando
    asyncio.run(args.func(args))


if __name__ == '__main__':
    main()
