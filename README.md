# MCP Server per l'Analisi del Codebase

Un server MCP (Model Context Protocol) locale che permette a Claude di analizzare, indicizzare e navigare il tuo codebase in modo intelligente.

## Panoramica del Progetto

Questo progetto implementa un server MCP in Python strutturato in 8 fasi progressive:

### Fase 1: Nucleo Base ✅ (implementata)
- Server MCP minimo funzionante
- Funzioni base: elenco file, lettura file
- Connessione a database SQLite

### Fase 2-8: In sviluppo
- Indicizzatore con embedding
- Parsing del codice con tree-sitter
- Ricerca semantica
- Aggiornamenti incrementali
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

### Avvio del Server MCP

```bash
# Imposta la directory del progetto (opzionale, default: directory corrente)
export MCP_PROJECT_ROOT=/path/to/your/project

# Avvia il server
python -m mcp_server.server
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
│   ├── server.py            # Server MCP principale
│   └── database.py          # Gestione database SQLite
├── mcp_data/                # Database e cache (generato automaticamente)
│   └── codebase.db         # Database SQLite
├── requirements.txt         # Dipendenze Python
├── .gitignore              # File da ignorare
└── README.md               # Questa documentazione
```

## Database

Il database SQLite memorizza:

- **files**: Informazioni sui file indicizzati
  - `path`: Percorso del file
  - `content_hash`: Hash SHA256 del contenuto
  - `summary`: Riassunto generato (Fase 2+)
  - `last_indexed`: Timestamp ultimo aggiornamento
  - `file_size`: Dimensione in byte
  - `language`: Linguaggio rilevato

## Sicurezza

- Il server accetta solo percorsi all'interno di `MCP_PROJECT_ROOT`
- File nascosti e directory di sistema sono esclusi automaticamente
- Supporta solo file di testo per evitare problemi con file binari

## Sviluppo

### Roadmap delle Fasi

- [x] Fase 1: Server MCP base
- [ ] Fase 2: Indicizzatore con embedding
- [ ] Fase 3: Parsing tree-sitter
- [ ] Fase 4: Ricerca semantica
- [ ] Fase 5: Aggiornamenti incrementali
- [ ] Fase 6: Analisi statica
- [ ] Fase 7: Integrazione Claude
- [ ] Fase 8: Documentazione finale

## Licenza

MIT License

## Contributi

Contributi sono benvenuti! Apri una issue o una pull request.
