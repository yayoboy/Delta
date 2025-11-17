# MCP Server per l'Analisi del Codebase

Un server MCP (Model Context Protocol) locale che permette a Claude di analizzare, indicizzare e navigare il tuo codebase in modo intelligente.

## Panoramica del Progetto

Questo progetto implementa un server MCP in Python strutturato in 8 fasi progressive:

### Fase 1: Nucleo Base ✅
- Server MCP minimo funzionante
- Funzioni base: elenco file, lettura file
- Connessione a database SQLite

### Fase 2: Indicizzatore ✅
- Scansione automatica del repository
- Calcolo hash e rilevamento linguaggi
- Generazione riassunti elementari
- Embedding con sentence-transformers (all-MiniLM-L6-v2)
- Aggiornamenti incrementali basati su hash
- CLI per gestione indicizzazione

### Fase 3-8: In sviluppo
- Parsing del codice con tree-sitter
- Ricerca semantica
- Analisi statica del codice
- Integrazione con Claude Desktop/CLI
- Documentazione completa

## Installazione

### Prerequisiti
- Python 3.10 o superiore
- pip

### Setup

```bash
# Clona il repository
git clone <repository-url>
cd Delta

# Crea un ambiente virtuale
python -m venv venv
source venv/bin/activate  # Su Windows: venv\Scripts\activate

# Installa le dipendenze
pip install -r requirements.txt
```

## Uso

### 1. Indicizzazione del Progetto

Prima di usare il server MCP, indicizza il tuo progetto:

```bash
# Indicizza il progetto corrente
python -m mcp_server.cli index

# Indicizza un progetto specifico
python -m mcp_server.cli index --project /path/to/project

# Forza re-indicizzazione completa
python -m mcp_server.cli index --force

# Mostra statistiche
python -m mcp_server.cli stats

# Elenca file indicizzati
python -m mcp_server.cli list

# Filtra per linguaggio
python -m mcp_server.cli list --language Python

# Mostra riassunti
python -m mcp_server.cli list -v
```

### 2. Avvio del Server MCP

```bash
# Imposta la directory del progetto (opzionale, default: directory corrente)
export MCP_PROJECT_ROOT=/path/to/your/project

# Avvia il server
python -m mcp_server
```

### Strumenti Disponibili (Fase 1)

1. **list_files** - Elenca tutti i file nel progetto
   - Parametri opzionali:
     - `pattern`: pattern per filtrare (es. "*.py")

2. **read_file** - Legge il contenuto di un file
   - Parametri richiesti:
     - `path`: percorso relativo del file

3. **get_indexed_files** - Mostra i file nel database
   - Nessun parametro

## Struttura del Progetto

```
Delta/
├── mcp_server/
│   ├── __init__.py          # Inizializzazione package
│   ├── __main__.py          # Entry point per python -m
│   ├── server.py            # Server MCP principale
│   ├── database.py          # Gestione database SQLite
│   ├── indexer.py           # Indicizzatore con embedding
│   └── cli.py               # CLI per gestione indicizzazione
├── mcp_data/                # Database e cache (generato automaticamente)
│   └── codebase.db         # Database SQLite
├── requirements.txt         # Dipendenze Python
├── setup.py                # Setup per installazione
├── .gitignore              # File da ignorare
└── README.md               # Questa documentazione
```

## Database

Il database SQLite memorizza:

### Tabella `files`
- `path`: Percorso del file
- `content_hash`: Hash SHA256 del contenuto
- `summary`: Riassunto generato automaticamente
- `last_indexed`: Timestamp ultimo aggiornamento
- `file_size`: Dimensione in byte
- `language`: Linguaggio rilevato

### Tabella `embeddings`
- `file_id`: Riferimento al file
- `embedding`: Vettore embedding (BLOB)
- `model_name`: Modello usato (all-MiniLM-L6-v2)
- `created_at`: Timestamp creazione

### Funzionalità Intelligenti

- **Aggiornamenti Incrementali**: Solo i file modificati vengono re-indicizzati
- **Rilevamento Linguaggio**: 20+ linguaggi supportati automaticamente
- **Riassunti Automatici**: Conta classi, funzioni, estrae primi commenti
- **Embedding Leggeri**: Modello compatto per ricerca semantica futura

## Sicurezza

- Il server accetta solo percorsi all'interno di `MCP_PROJECT_ROOT`
- File nascosti e directory di sistema sono esclusi automaticamente
- Supporta solo file di testo per evitare problemi con file binari

## Sviluppo

### Roadmap delle Fasi

- [x] Fase 1: Server MCP base
- [x] Fase 2: Indicizzatore con embedding
- [ ] Fase 3: Parsing tree-sitter per simboli e relazioni
- [ ] Fase 4: Ricerca semantica avanzata
- [ ] Fase 5: Ottimizzazioni performance
- [ ] Fase 6: Analisi statica (Ruff, mypy, ESLint)
- [ ] Fase 7: Integrazione Claude Desktop/CLI
- [ ] Fase 8: Documentazione finale e ampliamenti

## Licenza

MIT License

## Contributi

Contributi sono benvenuti! Apri una issue o una pull request.
