"""
Gestione del database SQLite per l'indicizzazione del codebase.
"""

import aiosqlite
import os
from pathlib import Path
from typing import Optional, List, Dict, Any


class Database:
    """Gestisce la connessione e le operazioni sul database SQLite."""

    def __init__(self, db_path: str = "mcp_data/codebase.db"):
        """
        Inizializza il database.

        Args:
            db_path: Percorso del file database SQLite
        """
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

        # Indici per velocizzare le ricerche
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_files_path
            ON files(path)
        """)

        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_file_id
            ON embeddings(file_id)
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
