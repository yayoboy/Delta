# Configurazione Claude Desktop (Installazione Globale)

## Configurazione Base - Auto-detect (Consigliata)

Il modo più semplice: il server rileva automaticamente la directory di lavoro di Claude!

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

**Vantaggi:**
- ✅ Nessuna configurazione manuale del progetto
- ✅ Funziona automaticamente con qualsiasi progetto
- ✅ Claude usa la directory corrente dove sta lavorando

**Nota:** Assicurati di aver indicizzato il progetto prima: `mcp-index index --project /path/to/project`

---

## Configurazione con Progetto Fisso

Se vuoi sempre analizzare un progetto specifico:

## Configurazione con Progetto Fisso

Se vuoi sempre analizzare un progetto specifico:

### Tutte le Piattaforme

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

## Esempi Specifici per Piattaforma

### macOS

File: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "codebase": {
      "command": "mcp-codebase",
      "args": [],
      "env": {
        "MCP_PROJECT_ROOT": "/Users/tuonome/progetti/mio-app"
      }
    }
  }
}
```

### Linux

File: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "codebase": {
      "command": "mcp-codebase",
      "args": [],
      "env": {
        "MCP_PROJECT_ROOT": "/home/tuonome/progetti/mio-app"
      }
    }
  }
}
```

### Windows

File: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "codebase": {
      "command": "mcp-codebase",
      "args": [],
      "env": {
        "MCP_PROJECT_ROOT": "C:/Users/TuoNome/progetti/mio-app"
      }
    }
  }
}
```

**Nota Windows:** Usa `/` invece di `\\` nei path, funziona meglio.

## Analizzare Progetti Multipli

### Opzione 1: Cambiare MCP_PROJECT_ROOT

1. Edita `claude_desktop_config.json`
2. Cambia solo `MCP_PROJECT_ROOT`
3. Riavvia Claude Desktop

### Opzione 2: Server Multipli (Avanzato)

```json
{
  "mcpServers": {
    "progetto-A": {
      "command": "mcp-codebase",
      "env": {
        "MCP_PROJECT_ROOT": "/path/to/progetto-A"
      }
    },
    "progetto-B": {
      "command": "mcp-codebase",
      "env": {
        "MCP_PROJECT_ROOT": "/path/to/progetto-B"
      }
    }
  }
}
```

Claude avrà accesso a entrambi i progetti contemporaneamente!

## Verifica Installazione

```bash
# Verifica che il comando sia disponibile
which mcp-codebase
# Output: /usr/local/bin/mcp-codebase (o simile)

# Testa la CLI
mcp-index --help

# Indicizza un progetto
mcp-index index --project /path/to/project
```

## Troubleshooting

**Comando non trovato:**
```bash
pip show mcp-codebase-server
pip install -e /path/to/Delta
```

**Log Claude Desktop:**
- macOS/Linux: Help → View Logs
- Windows: Help → View Logs
- Cerca "codebase" o errori MCP

**Test manuale:**
```bash
export MCP_PROJECT_ROOT=/path/to/project
mcp-codebase
# Dovrebbe avviarsi senza errori
```
