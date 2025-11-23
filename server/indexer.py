"""
Indicizzatore del codebase.

Scansiona il repository, calcola hash, genera riassunti e crea embedding
per ogni file di codice rilevante.
"""

import os
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Optional, Set
import asyncio

import numpy as np
from sentence_transformers import SentenceTransformer

from database import Database
from server import is_text_file, calculate_file_hash

try:
    from parser import CodeParser
    PARSER_AVAILABLE = True
except ImportError:
    PARSER_AVAILABLE = False
    CodeParser = None


class CodebaseIndexer:
    """Gestisce l'indicizzazione del codebase."""

    def __init__(
        self,
        project_root: str,
        db: Database,
        model_name: str = "all-MiniLM-L6-v2"
    ):
        """
        Inizializza l'indicizzatore.

        Args:
            project_root: Percorso radice del progetto
            db: Istanza del database
            model_name: Nome del modello sentence-transformers
        """
        self.project_root = Path(project_root).resolve()
        self.db = db
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.parser: Optional['CodeParser'] = None

        # Directory e file da escludere
        self.exclude_dirs = {
            '.git', '.venv', 'venv', '__pycache__', 'node_modules',
            '.idea', '.vscode', 'dist', 'build', '.eggs', 'egg-info',
            'mcp_data', '.mcp_cache', '.pytest_cache', '.tox'
        }

        self.exclude_files = {
            '.DS_Store', 'Thumbs.db', '.gitignore', '.dockerignore'
        }

        # Estensioni per linguaggi
        self.language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript',
            '.java': 'Java',
            '.c': 'C',
            '.cpp': 'C++',
            '.h': 'C/C++ Header',
            '.hpp': 'C++ Header',
            '.cs': 'C#',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.json': 'JSON',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.toml': 'TOML',
            '.xml': 'XML',
            '.md': 'Markdown',
            '.sql': 'SQL',
            '.sh': 'Shell',
            '.bash': 'Bash',
        }

    def load_model(self):
        """Carica il modello sentence-transformers."""
        if not self.model:
            print(f"Caricamento modello: {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            print("Modello caricato.")

    def load_parser(self):
        """Carica il parser tree-sitter."""
        if PARSER_AVAILABLE and not self.parser:
            try:
                print("Caricamento parser tree-sitter...")
                self.parser = CodeParser()
                print("Parser caricato.")
            except Exception as e:
                print(f"Avviso: impossibile caricare parser: {e}")
                self.parser = None

    def detect_language(self, file_path: Path) -> Optional[str]:
        """
        Rileva il linguaggio di programmazione di un file.

        Args:
            file_path: Percorso del file

        Returns:
            Nome del linguaggio o None
        """
        suffix = file_path.suffix.lower()
        return self.language_map.get(suffix)

    def generate_summary(self, content: str, language: Optional[str]) -> str:
        """
        Genera un riassunto elementare del file.

        Args:
            content: Contenuto del file
            language: Linguaggio rilevato

        Returns:
            Riassunto del file
        """
        lines = content.split('\n')
        total_lines = len(lines)
        non_empty_lines = len([l for l in lines if l.strip()])

        # Conta le definizioni principali
        if language in ['Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C#', 'Go', 'Rust']:
            classes = len(re.findall(r'\bclass\s+\w+', content))
            functions = len(re.findall(r'\b(def|function|func|fn)\s+\w+', content))

            summary = f"{language} file con {total_lines} righe"
            if classes > 0:
                summary += f", {classes} class{'i' if classes > 1 else 'e'}"
            if functions > 0:
                summary += f", {functions} funzion{'i' if functions > 1 else 'e'}"

        elif language == 'Markdown':
            headers = len(re.findall(r'^#+\s+.+$', content, re.MULTILINE))
            summary = f"Documento Markdown con {total_lines} righe e {headers} sezioni"

        elif language in ['JSON', 'YAML', 'TOML', 'XML']:
            summary = f"File di configurazione {language} con {total_lines} righe"

        else:
            summary = f"File di testo con {total_lines} righe ({non_empty_lines} non vuote)"

        # Estrai il primo commento/docstring se presente
        first_comment = self._extract_first_comment(content, language)
        if first_comment:
            summary += f". {first_comment[:100]}"

        return summary

    def _extract_first_comment(self, content: str, language: Optional[str]) -> Optional[str]:
        """
        Estrae il primo commento significativo dal file.

        Args:
            content: Contenuto del file
            language: Linguaggio del file

        Returns:
            Primo commento o None
        """
        if language in ['Python']:
            # Cerca docstring
            match = re.search(r'^\s*"""(.+?)"""', content, re.DOTALL | re.MULTILINE)
            if match:
                return match.group(1).strip()
            match = re.search(r"^\s*'''(.+?)'''", content, re.DOTALL | re.MULTILINE)
            if match:
                return match.group(1).strip()
            # Cerca commenti #
            match = re.search(r'^\s*#\s*(.+)$', content, re.MULTILINE)
            if match:
                return match.group(1).strip()

        elif language in ['JavaScript', 'TypeScript', 'Java', 'C', 'C++', 'C#', 'Go', 'Rust']:
            # Cerca commenti /** ... */
            match = re.search(r'/\*\*(.+?)\*/', content, re.DOTALL)
            if match:
                return match.group(1).strip()
            # Cerca commenti //
            match = re.search(r'^\s*//\s*(.+)$', content, re.MULTILINE)
            if match:
                return match.group(1).strip()

        return None

    def create_embedding(self, text: str) -> np.ndarray:
        """
        Crea un embedding per il testo fornito.

        Args:
            text: Testo da codificare

        Returns:
            Array numpy con l'embedding
        """
        if not self.model:
            self.load_model()

        # Limita la lunghezza del testo (il modello ha limiti)
        max_length = 5000
        if len(text) > max_length:
            text = text[:max_length]

        embedding = self.model.encode(text, show_progress_bar=False)
        return embedding

    def should_index_file(self, file_path: Path) -> bool:
        """
        Determina se un file dovrebbe essere indicizzato.

        Args:
            file_path: Percorso del file

        Returns:
            True se il file dovrebbe essere indicizzato
        """
        # Salta file nascosti
        if file_path.name.startswith('.'):
            return False

        # Salta file nella blacklist
        if file_path.name in self.exclude_files:
            return False

        # Salta file binari
        if not is_text_file(str(file_path)):
            return False

        # Salta file troppo grandi (>1MB)
        try:
            if file_path.stat().st_size > 1_000_000:
                return False
        except OSError:
            return False

        return True

    def find_files(self) -> List[Path]:
        """
        Trova tutti i file da indicizzare nel progetto.

        Returns:
            Lista di percorsi dei file
        """
        files = []

        for root, dirs, filenames in os.walk(self.project_root):
            # Rimuovi directory da escludere
            dirs[:] = [
                d for d in dirs
                if d not in self.exclude_dirs and not d.startswith('.')
            ]

            for filename in filenames:
                file_path = Path(root) / filename

                if self.should_index_file(file_path):
                    files.append(file_path)

        return sorted(files)

    async def index_file(self, file_path: Path, force: bool = False) -> bool:
        """
        Indicizza un singolo file.

        Args:
            file_path: Percorso del file
            force: Se True, forza la re-indicizzazione anche se l'hash non è cambiato

        Returns:
            True se il file è stato indicizzato, False se saltato
        """
        try:
            # Calcola hash
            content_hash = calculate_file_hash(str(file_path))

            # Percorso relativo
            rel_path = str(file_path.relative_to(self.project_root))

            # Verifica se il file esiste già nel database
            existing = await self.db.get_file_by_path(rel_path)

            if existing and existing['content_hash'] == content_hash and not force:
                # File non cambiato, skip
                return False

            # Leggi il contenuto
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Rileva linguaggio
            language = self.detect_language(file_path)

            # Genera riassunto
            summary = self.generate_summary(content, language)

            # Salva nel database
            file_size = file_path.stat().st_size
            await self.db.upsert_file(
                path=rel_path,
                content_hash=content_hash,
                summary=summary,
                file_size=file_size,
                language=language
            )

            # Crea embedding
            # Combina percorso, riassunto e contenuto (parziale)
            text_for_embedding = f"{rel_path}\n{summary}\n{content[:2000]}"
            embedding = self.create_embedding(text_for_embedding)

            # Serializza embedding
            embedding_bytes = embedding.tobytes()

            # Ottieni l'ID del file
            file_id = await self.db.get_file_id_by_path(rel_path)

            # Salva embedding
            if file_id:
                await self.db.upsert_embedding(
                    file_id=file_id,
                    embedding=embedding_bytes,
                    model_name=self.model_name
                )

                # Parse del codice per estrarre simboli
                if self.parser and language:
                    try:
                        symbols, references = self.parser.parse_file(content, language)

                        # Elimina simboli vecchi
                        await self.db.delete_symbols_for_file(file_id)

                        # Inserisci nuovi simboli
                        symbol_map = {}  # Mappa nome -> ID per gestire parent_id
                        for symbol in symbols:
                            parent_id = None
                            if symbol.parent_name and symbol.parent_name in symbol_map:
                                parent_id = symbol_map[symbol.parent_name]

                            symbol_id = await self.db.insert_symbol(
                                file_id=file_id,
                                name=symbol.name,
                                kind=symbol.kind,
                                start_line=symbol.start_line,
                                end_line=symbol.end_line,
                                start_col=symbol.start_col,
                                end_col=symbol.end_col,
                                docstring=symbol.docstring,
                                signature=symbol.signature,
                                parent_id=parent_id
                            )

                            symbol_map[symbol.name] = symbol_id

                        # Inserisci referenze
                        for ref in references:
                            if ref.from_symbol in symbol_map:
                                await self.db.insert_reference(
                                    from_symbol_id=symbol_map[ref.from_symbol],
                                    to_symbol_name=ref.to_symbol,
                                    reference_type=ref.reference_type,
                                    line=ref.line
                                )

                    except Exception as e:
                        print(f"  ⚠ Errore nel parsing: {e}")

            print(f"✓ Indicizzato: {rel_path}")
            return True

        except Exception as e:
            print(f"✗ Errore nell'indicizzare {file_path}: {e}")
            return False

    async def index_all(self, force: bool = False) -> Dict[str, int]:
        """
        Indicizza tutti i file nel progetto.

        Args:
            force: Se True, forza la re-indicizzazione di tutti i file

        Returns:
            Dizionario con statistiche dell'indicizzazione
        """
        print(f"\nIndicizzazione del progetto: {self.project_root}")
        print("=" * 60)

        # Carica il modello e il parser una volta sola
        self.load_model()
        self.load_parser()

        # Trova tutti i file
        files = self.find_files()
        print(f"\nTrovati {len(files)} file da analizzare\n")

        # Indicizza ogni file
        indexed = 0
        skipped = 0

        for file_path in files:
            was_indexed = await self.index_file(file_path, force=force)
            if was_indexed:
                indexed += 1
            else:
                skipped += 1

        print("\n" + "=" * 60)
        print(f"Indicizzazione completata:")
        print(f"  - File indicizzati: {indexed}")
        print(f"  - File saltati (non modificati): {skipped}")
        print(f"  - Totale: {len(files)}")

        return {
            'indexed': indexed,
            'skipped': skipped,
            'total': len(files)
        }


async def main():
    """Entry point per eseguire l'indicizzatore da CLI."""
    import sys

    project_root = os.environ.get("MCP_PROJECT_ROOT", os.getcwd())
    force = "--force" in sys.argv

    print(f"Directory progetto: {project_root}")
    print(f"Modalità: {'Force re-index' if force else 'Incrementale'}")

    # Inizializza database
    db = Database()
    await db.connect()

    try:
        # Crea e avvia l'indicizzatore
        indexer = CodebaseIndexer(project_root, db)
        await indexer.index_all(force=force)

    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
