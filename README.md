# MCP Server per Analisi del Codebase

Server MCP che permette a Claude di analizzare, indicizzare e navigare il tuo codebase.

## Caratteristiche

✅ **10 Strumenti MCP** - Ricerca simboli, analisi semantica, linting
✅ **9 Linguaggi** - Python, JS/TS, Java, C/C++, Go, Rust + altri
✅ **Ricerca Semantica** - Embedding AI con sentence-transformers
✅ **Analisi Statica** - Ruff, mypy, pylint, ESLint
✅ **Database Indicizzato** - SQLite con simboli, embedding, relazioni
✅ **Aggiornamenti Incrementali** - Solo file modificati vengono re-indicizzati

## Quick Start

```bash
# 1. Installa
git clone <repo>
cd Delta
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Indicizza progetto
python -m mcp_server.cli index --project /path/to/project

# 3. Avvia server MCP
export MCP_PROJECT_ROOT=/path/to/project
python -m mcp_server
```

## Configurazione Claude Desktop

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "codebase": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "env": {
        "MCP_PROJECT_ROOT": "/path/to/your/project"
      }
    }
  }
}
```

Riavvia Claude Desktop.

## Strumenti MCP Disponibili

| Strumento | Descrizione |
|-----------|-------------|
| `list_files` | Elenca file con pattern matching |
| `read_file` | Legge contenuto file |
| `get_indexed_files` | Mostra file indicizzati con riassunti |
| `search_symbols` | Cerca classi/funzioni per nome |
| `get_file_symbols` | Struttura completa di un file |
| `semantic_search` | Ricerca AI basata su contenuto |
| `get_symbol_references` | Analisi dipendenze codice |
| `lint_python` | Analisi statica Python (Ruff/mypy/pylint) |
| `lint_javascript` | ESLint per JS/TS |
| `get_available_linters` | Verifica tool installati |

## Esempi d'Uso con Claude

```
User: Mostrami tutti i file Python nel progetto
→ Claude usa list_files(pattern="*.py")

User: Cerca la classe Database
→ Claude usa search_symbols(query="Database", kind="class")

User: Trova file che gestiscono autenticazione
→ Claude usa semantic_search(query="authentication and login")

User: Analizza il codice per errori
→ Claude usa lint_python()

User: Mostrami la struttura di server.py
→ Claude usa get_file_symbols(path="mcp_server/server.py")
```

## CLI Commands

```bash
# Indicizza progetto
python -m mcp_server.cli index [--project PATH] [--force]

# Statistiche
python -m mcp_server.cli stats

# Elenca file indicizzati
python -m mcp_server.cli list [--language Python] [-v]
```

## Architettura

```
mcp_server/
├── server.py      # Server MCP principale (10 strumenti)
├── database.py    # SQLite (4 tabelle: files, embeddings, symbols, references)
├── indexer.py     # Scansione e indicizzazione con embedding
├── parser.py      # Parsing tree-sitter per 9 linguaggi
├── linters.py     # Integrazione Ruff, mypy, pylint, ESLint
└── cli.py         # Comandi CLI
```

### Database Schema

- **files**: path, hash, summary, language, file_size
- **embeddings**: file_id, embedding (BLOB), model_name
- **symbols**: name, kind, line, docstring, signature, parent_id
- **references**: from_symbol_id, to_symbol_name, reference_type, line

## Linguaggi Supportati

**Parsing completo:** Python, JavaScript, TypeScript, Java, C, C++, Go, Rust, Ruby
**Rilevamento:** +20 linguaggi (PHP, Swift, Kotlin, Scala, HTML, CSS, SQL, Shell, etc.)

## Strumenti Opzionali

```bash
# Python linting
pip install ruff mypy pylint

# JavaScript linting
npm install -g eslint prettier
```

## Performance

| Progetto | Indicizzazione | search_symbols | semantic_search |
|----------|----------------|----------------|-----------------|
| <100 file | 10-30s | <100ms | 500ms-2s |
| >1000 file | 5-10min | <500ms | 3-10s |

## Troubleshooting

**Server non si avvia:**
```bash
python --version  # Verifica Python 3.10+
pip list          # Verifica dipendenze
```

**Tree-sitter errori:**
```bash
pip install --force-reinstall tree-sitter-python tree-sitter-javascript
```

**Database vuoto:**
```bash
python -m mcp_server.cli index --force
```

## Variabili d'Ambiente

```bash
export MCP_PROJECT_ROOT=/path/to/project              # (richiesto)
export MCP_DATABASE_PATH=mcp_data/codebase.db        # (opzionale)
export MCP_EMBEDDING_MODEL=all-MiniLM-L6-v2          # (opzionale)
```

## Sicurezza

- ✅ Sandbox: accesso limitato a `MCP_PROJECT_ROOT`
- ✅ Path validation: nessun path traversal
- ✅ SQL injection: query parametrizzate
- ✅ File binari esclusi automaticamente

## Limitazioni

- File >1MB non indicizzati (performance)
- Solo file di testo supportati
- Ricerca semantica può essere lenta su progetti enormi (>10k file)

## Implementazione (8 Fasi)

✅ **Fase 1:** Server MCP base con database SQLite
✅ **Fase 2:** Indicizzatore con embedding e hash
✅ **Fase 3:** Parsing tree-sitter per simboli
✅ **Fase 4:** Interfaccia MCP avanzata (10 strumenti)
✅ **Fase 5:** Ottimizzazioni incrementali
✅ **Fase 6:** Analisi statica (Ruff, mypy, ESLint)
✅ **Fase 7:** Integrazione Claude Desktop
✅ **Fase 8:** Documentazione completa

## Versione

**0.6.0** - Progetto completo e production-ready

## License

MIT
