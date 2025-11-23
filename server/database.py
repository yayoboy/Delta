"""
Gestione del database SQLite per l'indicizzazione del codebase.
"""

import aiosqlite
import os
from pathlib import Path
from typing import Optional, List, Dict, Any


class Database:
    """Gestisce la connessione e le operazioni sul database SQLite."""

    def __init__(self, db_path: str = None):
        """
        Inizializza il database.

        Args:
            db_path: Percorso del file database SQLite (default: ~/.mcp_codebase/db.sqlite)
        """
        if db_path is None:
            # Usa directory home per database globale
            home = os.path.expanduser("~")
            db_dir = os.path.join(home, ".mcp_codebase")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "codebase.db")

        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None

        # Assicura che la directory esista
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    async def connect(self):
        """Apre la connessione al database."""
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self._initialize_schema()

    async def close(self):
        """Chiude la connessione al database."""
        if self.db:
            await self.db.close()

    async def _initialize_schema(self):
        """Crea le tabelle se non esistono."""
        # Tabella per i file indicizzati
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                content_hash TEXT NOT NULL,
                summary TEXT,
                last_indexed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_size INTEGER,
                language TEXT
            )
        """)

        # Tabella per gli embedding dei file
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                embedding BLOB NOT NULL,
                model_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            )
        """)

        # Tabella per i simboli (classi, funzioni, variabili)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                kind TEXT NOT NULL,
                start_line INTEGER,
                end_line INTEGER,
                start_col INTEGER,
                end_col INTEGER,
                docstring TEXT,
                signature TEXT,
                parent_id INTEGER,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
                FOREIGN KEY (parent_id) REFERENCES symbols(id) ON DELETE CASCADE
            )
        """)

        # Tabella per le relazioni tra simboli
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS references (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_symbol_id INTEGER NOT NULL,
                to_symbol_name TEXT NOT NULL,
                reference_type TEXT NOT NULL,
                line INTEGER,
                FOREIGN KEY (from_symbol_id) REFERENCES symbols(id) ON DELETE CASCADE
            )
        """)

        # Indici per velocizzare le ricerche
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_files_path
            ON files(path)
        """)

        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_file_id
            ON embeddings(file_id)
        """)

        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_symbols_file_id
            ON symbols(file_id)
        """)

        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_symbols_name
            ON symbols(name)
        """)

        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_references_from
            ON references(from_symbol_id)
        """)

        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_references_to
            ON references(to_symbol_name)
        """)

        await self.db.commit()

    async def get_all_files(self) -> List[Dict[str, Any]]:
        """
        Recupera tutti i file indicizzati.

        Returns:
            Lista di dizionari con le informazioni sui file
        """
        async with self.db.execute(
            "SELECT * FROM files ORDER BY path"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_file_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Recupera un file specifico per percorso.

        Args:
            path: Percorso del file

        Returns:
            Dizionario con le informazioni sul file o None
        """
        async with self.db.execute(
            "SELECT * FROM files WHERE path = ?", (path,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def upsert_file(
        self,
        path: str,
        content_hash: str,
        summary: Optional[str] = None,
        file_size: Optional[int] = None,
        language: Optional[str] = None
    ):
        """
        Inserisce o aggiorna un file nel database.

        Args:
            path: Percorso del file
            content_hash: Hash del contenuto
            summary: Riassunto del file
            file_size: Dimensione del file in byte
            language: Linguaggio di programmazione rilevato
        """
        await self.db.execute("""
            INSERT INTO files (path, content_hash, summary, file_size, language)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                content_hash = excluded.content_hash,
                summary = excluded.summary,
                file_size = excluded.file_size,
                language = excluded.language,
                last_indexed = CURRENT_TIMESTAMP
        """, (path, content_hash, summary, file_size, language))

        await self.db.commit()

    async def delete_file(self, path: str):
        """
        Rimuove un file dal database.

        Args:
            path: Percorso del file da rimuovere
        """
        await self.db.execute("DELETE FROM files WHERE path = ?", (path,))
        await self.db.commit()

    async def get_file_id_by_path(self, path: str) -> Optional[int]:
        """
        Recupera l'ID di un file per percorso.

        Args:
            path: Percorso del file

        Returns:
            ID del file o None
        """
        async with self.db.execute(
            "SELECT id FROM files WHERE path = ?", (path,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

    async def upsert_embedding(
        self,
        file_id: int,
        embedding: bytes,
        model_name: str
    ):
        """
        Inserisce o aggiorna l'embedding di un file.

        Args:
            file_id: ID del file
            embedding: Embedding serializzato come bytes
            model_name: Nome del modello usato
        """
        # Prima elimina eventuali embedding esistenti per questo file
        await self.db.execute(
            "DELETE FROM embeddings WHERE file_id = ?", (file_id,)
        )

        # Inserisci il nuovo embedding
        await self.db.execute("""
            INSERT INTO embeddings (file_id, embedding, model_name)
            VALUES (?, ?, ?)
        """, (file_id, embedding, model_name))

        await self.db.commit()

    async def get_embedding(self, file_id: int) -> Optional[Dict[str, Any]]:
        """
        Recupera l'embedding di un file.

        Args:
            file_id: ID del file

        Returns:
            Dizionario con i dati dell'embedding o None
        """
        async with self.db.execute(
            "SELECT * FROM embeddings WHERE file_id = ?", (file_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def delete_symbols_for_file(self, file_id: int):
        """
        Elimina tutti i simboli associati a un file.

        Args:
            file_id: ID del file
        """
        await self.db.execute("DELETE FROM symbols WHERE file_id = ?", (file_id,))
        await self.db.commit()

    async def insert_symbol(
        self,
        file_id: int,
        name: str,
        kind: str,
        start_line: int,
        end_line: int,
        start_col: int = 0,
        end_col: int = 0,
        docstring: Optional[str] = None,
        signature: Optional[str] = None,
        parent_id: Optional[int] = None
    ) -> int:
        """
        Inserisce un nuovo simbolo nel database.

        Args:
            file_id: ID del file
            name: Nome del simbolo
            kind: Tipo di simbolo (class, function, method, variable, etc.)
            start_line: Linea di inizio
            end_line: Linea di fine
            start_col: Colonna di inizio
            end_col: Colonna di fine
            docstring: Documentazione del simbolo
            signature: Firma del simbolo
            parent_id: ID del simbolo genitore (per metodi, nested functions, etc.)

        Returns:
            ID del simbolo inserito
        """
        cursor = await self.db.execute("""
            INSERT INTO symbols (
                file_id, name, kind, start_line, end_line,
                start_col, end_col, docstring, signature, parent_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_id, name, kind, start_line, end_line,
            start_col, end_col, docstring, signature, parent_id
        ))

        await self.db.commit()
        return cursor.lastrowid

    async def insert_reference(
        self,
        from_symbol_id: int,
        to_symbol_name: str,
        reference_type: str,
        line: int
    ):
        """
        Inserisce una referenza tra simboli.

        Args:
            from_symbol_id: ID del simbolo che fa riferimento
            to_symbol_name: Nome del simbolo referenziato
            reference_type: Tipo di referenza (call, import, extends, etc.)
            line: Linea dove avviene la referenza
        """
        await self.db.execute("""
            INSERT INTO references (from_symbol_id, to_symbol_name, reference_type, line)
            VALUES (?, ?, ?, ?)
        """, (from_symbol_id, to_symbol_name, reference_type, line))

        await self.db.commit()

    async def get_symbols_by_file(self, file_id: int) -> List[Dict[str, Any]]:
        """
        Recupera tutti i simboli di un file.

        Args:
            file_id: ID del file

        Returns:
            Lista di simboli
        """
        async with self.db.execute(
            "SELECT * FROM symbols WHERE file_id = ? ORDER BY start_line",
            (file_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def search_symbols_by_name(self, pattern: str) -> List[Dict[str, Any]]:
        """
        Cerca simboli per nome (con LIKE).

        Args:
            pattern: Pattern di ricerca SQL (es. "%MyClass%")

        Returns:
            Lista di simboli con informazioni sul file
        """
        async with self.db.execute("""
            SELECT s.*, f.path as file_path, f.language
            FROM symbols s
            JOIN files f ON s.file_id = f.id
            WHERE s.name LIKE ?
            ORDER BY s.name
        """, (pattern,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_references_from_symbol(self, symbol_id: int) -> List[Dict[str, Any]]:
        """
        Recupera tutte le referenze da un simbolo.

        Args:
            symbol_id: ID del simbolo

        Returns:
            Lista di referenze
        """
        async with self.db.execute(
            "SELECT * FROM references WHERE from_symbol_id = ?",
            (symbol_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
