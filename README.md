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

### Installazione Globale (una volta sola)

```bash
# 1. Clona e installa il server MCP globalmente
git clone <repo>
cd Delta
pip install -e .

# Verifica installazione
which mcp-codebase  # Dovrebbe mostrare il path del comando
mcp-index --help    # Mostra help della CLI
```

### Uso con Qualsiasi Progetto

```bash
# Indicizza il progetto che vuoi analizzare
mcp-index index --project /path/to/your/project

# Statistiche
mcp-index stats

# Elenca file indicizzati
mcp-index list
```

### Configurazione Claude Desktop (una volta sola)

Edita il file di configurazione per la tua piattaforma:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

**Opzione 1 - Auto-detect (semplice):**
```json
{
  "mcpServers": {
    "codebase": {
      "command": "mcp-codebase",
      "args": []
    }
  }
}
```
Il server userà automaticamente la directory di lavoro corrente di Claude!

**Opzione 2 - Progetto specifico:**
```json
{
  "mcpServers": {
    "codebase": {
      "command": "mcp-codebase",
      "args": [],
      "env": {
        "MCP_PROJECT_ROOT": "/path/to/your/project"
      }
    }
  }
}
```

**Riavvia Claude Desktop** - il server si avvia automaticamente!

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

Dopo l'installazione globale, usa i comandi `mcp-index`:

```bash
# Indicizza progetto
mcp-index index --project /path/to/project [--force]

# Cambia progetto
mcp-index index --project /path/to/altro-progetto

# Statistiche database corrente
mcp-index stats

# Elenca file indicizzati
mcp-index list [--language Python] [-v]
```

**Il database viene creato in:** `~/.mcp_codebase/` (un database per progetto)

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

**Comando mcp-codebase non trovato:**
```bash
pip install -e .          # Reinstalla
pip show mcp-codebase-server  # Verifica installazione
```

**Claude non vede il server MCP:**
- Usa semplicemente `"command": "mcp-codebase"` nel config
- Verifica che `which mcp-codebase` mostri il comando
- Controlla i log: Help → View Logs in Claude Desktop
- Riavvia Claude Desktop dopo modifiche al config

**Cambiare progetto da analizzare:**
1. Cambia `MCP_PROJECT_ROOT` nel config di Claude Desktop
2. Esegui `mcp-index index --project /nuovo/progetto`
3. Riavvia Claude Desktop

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
# Progetto da analizzare (opzionale - usa cwd se non specificato)
export MCP_PROJECT_ROOT=/path/to/project

# Database personalizzato (opzionale, default: ~/.mcp_codebase/)
export MCP_DATABASE_PATH=/custom/path/db.sqlite

# Modello embedding (opzionale, default: all-MiniLM-L6-v2)
export MCP_EMBEDDING_MODEL=all-MiniLM-L6-v2
```

**Nota:** Se `MCP_PROJECT_ROOT` non è specificato, il server usa la directory corrente!

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
