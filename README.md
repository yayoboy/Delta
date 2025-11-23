# Codebase Analyzer - Claude Desktop Extension

Estensione Claude Desktop per analizzare, indicizzare e navigare il codebase con ricerca semantica e parsing AST.

## Caratteristiche

- **12 Strumenti MCP** - Ricerca simboli, analisi semantica, linting, cambio progetto dinamico
- **9 Linguaggi** - Python, JS/TS, Java, C/C++, Go, Rust, Ruby
- **Ricerca Semantica** - Embedding AI con sentence-transformers
- **Analisi Statica** - Ruff, mypy, pylint, ESLint
- **Database Indicizzato** - SQLite con simboli, embedding, relazioni
- **Aggiornamenti Incrementali** - Solo file modificati vengono re-indicizzati

## Installazione

### Metodo 1: Desktop Extension (Consigliato)

1. **Scarica** il file `.mcpb` dalla release
2. **Doppio click** sul file
3. **Clicca "Install"** nel dialog di Claude Desktop

L'estensione si configura automaticamente!

### Metodo 2: Build Manuale

```bash
# Clona il repository
git clone https://github.com/yayoboy/Delta
cd Delta

# Installa le dipendenze Python (sistema o venv)
pip install -r requirements.txt

# Crea il pacchetto .mcpb
python build.py

# Il file sarà in dist/codebase-analyzer-1.0.0.mcpb
```

### Metodo 3: Installazione Tradizionale

```bash
# Clona e installa
git clone https://github.com/yayoboy/Delta
cd Delta
pip install -e .

# Configura Claude Desktop manualmente
# Edita: ~/Library/Application Support/Claude/claude_desktop_config.json
```

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

## Strumenti MCP Disponibili

| Strumento | Descrizione |
|-----------|-------------|
| `set_project_directory` | **Cambia progetto dinamicamente** |
| `get_current_project` | Mostra progetto corrente e statistiche |
| `index_repository` | Indicizza tutti i file del repository |
| `search_code` | Ricerca semantica o testuale nel codice |
| `get_file_info` | Informazioni dettagliate su un file |
| `list_symbols` | Lista classi, funzioni, metodi |
| `get_symbol_details` | Dettagli completi su un simbolo |
| `find_references` | Trova referenze a un simbolo |
| `get_file_structure` | Struttura gerarchica di un file |
| `get_repository_stats` | Statistiche generali del repository |
| `run_linter` | Analisi statica del codice |
| `get_code_quality_report` | Report completo qualità codice |

## Esempi d'Uso

**Cambiare progetto:**
```
User: Lavora sul progetto in /Users/nome/app-frontend
Claude: [usa set_project_directory(path="/Users/nome/app-frontend")]
```

**Analizzare codice:**
```
User: Cerca la classe Database
Claude: [usa list_symbols(kind="class", query="Database")]

User: Trova file che gestiscono autenticazione
Claude: [usa search_code(query="authentication and login", semantic=true)]

User: Analizza il codice per errori
Claude: [usa run_linter(tool="ruff")]
```

## Build del Pacchetto

```bash
# Build standard
python build.py

# Con nome personalizzato
python build.py --output my-extension

# Con dipendenze bundle (file più grande)
python build.py --with-deps
```

Il pacchetto `.mcpb` viene creato in `dist/`.

## Struttura Progetto

```
Delta/
├── manifest.json      # Configurazione estensione MCPB
├── build.py          # Script per creare .mcpb
├── icon.svg          # Icona estensione
├── requirements.txt  # Dipendenze Python
├── server/
│   ├── main.py       # Entry point
│   ├── server.py     # Server MCP (12 strumenti)
│   ├── database.py   # SQLite (4 tabelle)
│   ├── indexer.py    # Indicizzazione con embedding
│   ├── parser.py     # Parsing tree-sitter
│   ├── linters.py    # Integrazione linter
│   └── cli.py        # Comandi CLI
└── README.md
```

## Linguaggi Supportati

**Parsing completo:** Python, JavaScript, TypeScript, Java, C, C++, Go, Rust, Ruby

**Rilevamento:** +20 linguaggi (PHP, Swift, Kotlin, Scala, HTML, CSS, SQL, Shell, etc.)

## Requisiti

- Python >= 3.9
- Claude Desktop >= 1.0.0

**Dipendenze Python:**
- mcp >= 1.0.0
- sentence-transformers >= 2.2.0
- tree-sitter >= 0.20.0
- aiosqlite >= 0.19.0
- numpy >= 1.24.0

**Strumenti Opzionali per Linting:**
```bash
pip install ruff mypy pylint          # Python
npm install -g eslint prettier        # JavaScript/TypeScript
```

## Piattaforme

- macOS
- Windows
- Linux

## Troubleshooting

**Estensione non si installa:**
- Verifica che Claude Desktop sia aggiornato
- Controlla che Python >= 3.9 sia installato

**Server non risponde:**
- Controlla i log: Help → View Logs in Claude Desktop
- Verifica le dipendenze: `pip install -r requirements.txt`

**Tree-sitter errori:**
```bash
pip install --force-reinstall tree-sitter-python tree-sitter-javascript
```

## Performance

| Progetto | Indicizzazione | Ricerca simboli | Ricerca semantica |
|----------|----------------|-----------------|-------------------|
| <100 file | 10-30s | <100ms | 500ms-2s |
| >1000 file | 5-10min | <500ms | 3-10s |

## Sicurezza

- Sandbox: accesso limitato alla directory progetto
- Path validation: nessun path traversal
- SQL injection: query parametrizzate
- File binari esclusi automaticamente

## Versione

**1.0.0** - Prima release come Desktop Extension

## License

MIT
