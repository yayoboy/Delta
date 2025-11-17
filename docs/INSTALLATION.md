# Guida all'Installazione

Guida completa per installare e configurare il server MCP per l'analisi del codebase.

## Requisiti di Sistema

### Software Richiesto
- Python 3.10 o superiore
- pip (package manager Python)
- Git

### Software Opzionale (per analisi statica)
- **Per Python:**
  - ruff (linting veloce)
  - mypy (type checking)
  - pylint (analisi completa)

- **Per JavaScript/TypeScript:**
  - Node.js e npm
  - ESLint
  - Prettier

## Installazione Base

### 1. Clona il Repository

```bash
git clone <repository-url>
cd Delta
```

### 2. Crea Ambiente Virtuale

```bash
# Crea venv
python -m venv venv

# Attiva venv
# Su Linux/Mac:
source venv/bin/activate

# Su Windows:
venv\Scripts\activate
```

### 3. Installa Dipendenze

```bash
pip install -r requirements.txt
```

Questo installerà:
- MCP SDK
- sentence-transformers (per embedding)
- tree-sitter + grammatiche (per parsing)
- aiosqlite (database)
- numpy, pydantic, python-dotenv

### 4. Verifica Installazione

```bash
python -m mcp_server.cli --help
```

Dovresti vedere l'help della CLI.

## Installazione Strumenti di Analisi (Opzionale)

### Python

```bash
pip install ruff mypy pylint
```

### JavaScript/TypeScript

```bash
npm install -g eslint prettier
```

## Configurazione

### Variabili d'Ambiente

Crea un file `.env` nella root del progetto:

```env
# Directory del progetto da analizzare
MCP_PROJECT_ROOT=/path/to/your/project

# Percorso database (opzionale, default: mcp_data/codebase.db)
MCP_DATABASE_PATH=mcp_data/codebase.db

# Modello embedding (opzionale, default: all-MiniLM-L6-v2)
MCP_EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Primo Utilizzo

### 1. Indicizza il Tuo Progetto

```bash
# Indicizza il progetto corrente
python -m mcp_server.cli index

# Oppure specifica un progetto
python -m mcp_server.cli index --project /path/to/project

# Forza re-indicizzazione completa
python -m mcp_server.cli index --force
```

### 2. Verifica l'Indicizzazione

```bash
# Mostra statistiche
python -m mcp_server.cli stats

# Elenca file indicizzati
python -m mcp_server.cli list

# Filtra per linguaggio
python -m mcp_server.cli list --language Python
```

### 3. Avvia il Server MCP

```bash
export MCP_PROJECT_ROOT=/path/to/project
python -m mcp_server
```

## Integrazione con Claude Desktop

### Configurazione macOS

Edita `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "codebase-analyzer": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "env": {
        "MCP_PROJECT_ROOT": "/path/to/your/project"
      }
    }
  }
}
```

### Configurazione Windows

Edita `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "codebase-analyzer": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "env": {
        "MCP_PROJECT_ROOT": "C:\\path\\to\\your\\project"
      }
    }
  }
}
```

### Configurazione Linux

Edita `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "codebase-analyzer": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "env": {
        "MCP_PROJECT_ROOT": "/path/to/your/project"
      }
    }
  }
}
```

## Verifica dell'Integrazione

1. Riavvia Claude Desktop
2. Apri una nuova conversazione
3. Claude dovrebbe mostrare che il server MCP è connesso
4. Prova a chiedere: "Quali file sono indicizzati nel progetto?"

## Risoluzione Problemi

### Il server non si avvia

- Verifica che Python 3.10+ sia installato: `python --version`
- Verifica che le dipendenze siano installate: `pip list`
- Controlla i log di Claude Desktop

### L'indicizzazione fallisce

- Verifica che il progetto sia accessibile
- Controlla i permessi delle directory
- Verifica spazio disco disponibile

### Tree-sitter non funziona

```bash
# Reinstalla le grammatiche
pip uninstall tree-sitter-python tree-sitter-javascript
pip install tree-sitter-python tree-sitter-javascript
```

### Embedding troppo lenti

- Usa un modello più leggero: `all-MiniLM-L6-v2` (default)
- Oppure disabilita embedding temporaneamente
- Considera l'uso di GPU se disponibile

## Prossimi Passi

- Leggi [USAGE.md](USAGE.md) per esempi d'uso
- Vedi [API.md](API.md) per riferimento completo MCP tools
- Consulta [EXAMPLES.md](EXAMPLES.md) per casi d'uso avanzati
