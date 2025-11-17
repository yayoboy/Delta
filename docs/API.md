# Riferimento API

Documentazione completa degli strumenti MCP esposti dal server.

## Strumenti MCP

### list_files

Elenca tutti i file nel progetto.

**Parametri:**
- `pattern` (string, opzionale): Pattern glob per filtrare file (es. "*.py")

**Output:**
```
Trovati 25 file nel progetto:

- mcp_server/__init__.py
- mcp_server/server.py
- mcp_server/database.py
...
```

**Esempio:**
```python
{
  "name": "list_files",
  "arguments": {
    "pattern": "*.py"
  }
}
```

---

### read_file

Legge il contenuto completo di un file.

**Parametri:**
- `path` (string, richiesto): Percorso relativo del file

**Output:**
```
Contenuto di mcp_server/server.py:

#!/usr/bin/env python3
...
```

**Esempio:**
```python
{
  "name": "read_file",
  "arguments": {
    "path": "mcp_server/server.py"
  }
}
```

---

### get_indexed_files

Recupera l'elenco di file indicizzati con metadati.

**Parametri:** Nessuno

**Output:**
```
File indicizzati nel database (25):

- mcp_server/__init__.py [Python]
  Riassunto: Python file con 5 righe

- mcp_server/server.py [Python]
  Riassunto: Python file con 361 righe, 12 funzioni
...
```

---

### search_symbols

Cerca simboli nel codebase per nome.

**Parametri:**
- `query` (string, richiesto): Nome o pattern del simbolo
- `kind` (string, opzionale): Tipo (class, function, method, etc.)

**Output:**
```
Trovati 3 simbolo/i per 'Database':

**Database** (class)
  File: mcp_server/database.py:15
  Doc: Gestisce la connessione e le operazioni sul database SQLite....

**init_database** (function)
  File: mcp_server/cli.py:45
  Firma: (db_path: str)
...
```

**Esempio:**
```python
{
  "name": "search_symbols",
  "arguments": {
    "query": "Database",
    "kind": "class"
  }
}
```

---

### get_file_symbols

Ottiene la struttura completa di un file.

**Parametri:**
- `path` (string, richiesto): Percorso relativo del file

**Output:**
```
Struttura di mcp_server/database.py:

## Classes

- Database (linea 15)
  └─ Gestisce la connessione e le operazioni sul database SQLite.

## Methods

  - __init__(self, db_path: str = "mcp_data/codebase.db") (linea 25)
    └─ Inizializza il database....

  - connect(self) (linea 28)
  - close(self) (linea 34)
...
```

**Esempio:**
```python
{
  "name": "get_file_symbols",
  "arguments": {
    "path": "mcp_server/database.py"
  }
}
```

---

### semantic_search

Ricerca semantica basata su embedding.

**Parametri:**
- `query` (string, richiesto): Descrizione in linguaggio naturale
- `limit` (integer, opzionale): Numero massimo risultati (default: 10)

**Output:**
```
Risultati ricerca semantica per 'database operations':

1. **mcp_server/database.py** [Python]
   Rilevanza: 87.5%
   Python file con 389 righe, 15 funzioni

2. **mcp_server/cli.py** [Python]
   Rilevanza: 72.3%
   Python file con 150 righe, 3 funzioni
...
```

**Esempio:**
```python
{
  "name": "semantic_search",
  "arguments": {
    "query": "database operations and SQL queries",
    "limit": 5
  }
}
```

---

### get_symbol_references

Trova tutte le referenze a un simbolo.

**Parametri:**
- `symbol_name` (string, richiesto): Nome del simbolo

**Output:**
```
Referenze per 'Database':

**Definizione:** mcp_server/database.py:15

Chiamate/import (3):
  - connect (call) alla linea 45
  - get_all_files (call) alla linea 89
  - upsert_file (call) alla linea 134
```

**Esempio:**
```python
{
  "name": "get_symbol_references",
  "arguments": {
    "symbol_name": "Database"
  }
}
```

---

### lint_python

Esegue analisi statica su codice Python.

**Parametri:**
- `target` (string, opzionale): File o directory specifici
- `fix` (boolean, opzionale): Auto-fix quando possibile (default: false)

**Output:**
```
Risultati analisi Python:

## RUFF

ERRORI (2):
**mcp_server/server.py:145:5**
  [ruff] F841: Local variable 'result' is assigned but never used

WARNINGS (3):
**mcp_server/indexer.py:89:0**
  [ruff] E501: Line too long (92 > 88 characters)
...

---

## MYPY

Nessun problema trovato! ✓

---

Totale problemi: 5
```

**Esempio:**
```python
{
  "name": "lint_python",
  "arguments": {
    "target": "mcp_server/server.py",
    "fix": true
  }
}
```

---

### lint_javascript

Esegue ESLint su JavaScript/TypeScript.

**Parametri:**
- `target` (string, opzionale): File o directory specifici
- `fix` (boolean, opzionale): Auto-fix quando possibile

**Output:**
```
Risultati analisi JavaScript/TypeScript:

## ESLINT

ERRORI (1):
**src/index.js:23:5**
  [eslint] no-unused-vars: 'result' is assigned but never used

WARNINGS (2):
**src/utils.js:45:10**
  [eslint] prefer-const: 'data' should be const
...

Totale problemi: 3
```

---

### get_available_linters

Mostra strumenti di analisi disponibili.

**Parametri:** Nessuno

**Output:**
```
Strumenti disponibili (4):

✓ ruff
✓ mypy
✓ pylint
✓ eslint
```

---

## Schema Database

### Tabella `files`

Metadati dei file indicizzati.

| Colonna | Tipo | Descrizione |
|---------|------|-------------|
| id | INTEGER | Primary key |
| path | TEXT | Percorso relativo |
| content_hash | TEXT | SHA256 hash |
| summary | TEXT | Riassunto auto-generato |
| last_indexed | TIMESTAMP | Ultimo aggiornamento |
| file_size | INTEGER | Dimensione in byte |
| language | TEXT | Linguaggio rilevato |

### Tabella `embeddings`

Vettori embedding per ricerca semantica.

| Colonna | Tipo | Descrizione |
|---------|------|-------------|
| id | INTEGER | Primary key |
| file_id | INTEGER | FK → files.id |
| embedding | BLOB | Vettore numpy serializzato |
| model_name | TEXT | Modello usato |
| created_at | TIMESTAMP | Data creazione |

### Tabella `symbols`

Simboli estratti dal parsing.

| Colonna | Tipo | Descrizione |
|---------|------|-------------|
| id | INTEGER | Primary key |
| file_id | INTEGER | FK → files.id |
| name | TEXT | Nome del simbolo |
| kind | TEXT | Tipo (class, function, etc.) |
| start_line | INTEGER | Linea inizio |
| end_line | INTEGER | Linea fine |
| start_col | INTEGER | Colonna inizio |
| end_col | INTEGER | Colonna fine |
| docstring | TEXT | Documentazione |
| signature | TEXT | Firma funzione/metodo |
| parent_id | INTEGER | FK → symbols.id (genitore) |

### Tabella `references`

Relazioni tra simboli.

| Colonna | Tipo | Descrizione |
|---------|------|-------------|
| id | INTEGER | Primary key |
| from_symbol_id | INTEGER | FK → symbols.id |
| to_symbol_name | TEXT | Nome simbolo referenziato |
| reference_type | TEXT | Tipo (call, import, etc.) |
| line | INTEGER | Linea della referenza |

---

## CLI Commands

### index

Indicizza il progetto.

```bash
python -m mcp_server.cli index [OPTIONS]

Opzioni:
  --project PATH    Percorso del progetto
  --force          Forza re-indicizzazione completa
  --db PATH        Percorso database custom
```

### stats

Mostra statistiche database.

```bash
python -m mcp_server.cli stats [OPTIONS]

Opzioni:
  --db PATH        Percorso database custom
```

### list

Elenca file indicizzati.

```bash
python -m mcp_server.cli list [OPTIONS]

Opzioni:
  --language LANG  Filtra per linguaggio
  -v, --verbose    Mostra riassunti
  --db PATH        Percorso database custom
```

---

## Variabili d'Ambiente

### MCP_PROJECT_ROOT
- **Tipo:** string (path)
- **Default:** `os.getcwd()`
- **Descrizione:** Directory radice del progetto da analizzare

### MCP_DATABASE_PATH
- **Tipo:** string (path)
- **Default:** `mcp_data/codebase.db`
- **Descrizione:** Percorso del database SQLite

### MCP_EMBEDDING_MODEL
- **Tipo:** string
- **Default:** `all-MiniLM-L6-v2`
- **Descrizione:** Nome modello sentence-transformers

---

## Errori Comuni

### "database not initialized"
Il server non ha accesso al database. Verifica che:
- Il database esista (`mcp_data/codebase.db`)
- Il progetto sia stato indicizzato
- I permessi siano corretti

### "file not found in database"
Il file non è stato indicizzato. Esegui:
```bash
python -m mcp_server.cli index --force
```

### "tool not available"
Strumento di linting non installato. Installa:
```bash
pip install ruff mypy pylint
npm install -g eslint
```

---

## Performance

### Tempi Tipici

| Operazione | Progetto Piccolo (<100 file) | Progetto Grande (>1000 file) |
|------------|------------------------------|------------------------------|
| Indicizzazione iniziale | 10-30s | 5-10min |
| Aggiornamento incrementale | 2-5s | 30-60s |
| search_symbols | <100ms | <500ms |
| semantic_search | 500ms-2s | 3-10s |
| lint_python | 2-5s | 10-30s |

### Ottimizzazioni

- **Cache embedding:** Gli embedding sono calcolati una sola volta
- **Indici database:** Query ottimizzate con indici
- **Aggiornamenti incrementali:** Solo file modificati
- **Lazy loading:** Modelli caricati on-demand

---

## Sicurezza

- **Sandbox:** Accesso solo a `MCP_PROJECT_ROOT`
- **Path traversal:** Verifiche su tutti i percorsi
- **SQL injection:** Query parametrizzate
- **File binari:** Esclusi automaticamente

---

## Versioning

Versione corrente: **0.6.0**

Schema versioning: `MAJOR.MINOR.PATCH`
- **MAJOR:** Breaking changes
- **MINOR:** Nuove funzionalità
- **PATCH:** Bug fix

---

## Support

- GitHub Issues: [repository-url/issues]
- Documentazione: [repository-url/docs]
- Discord: [link se disponibile]
