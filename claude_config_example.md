# Esempio configurazione Claude Desktop

## macOS/Linux

```json
{
  "mcpServers": {
    "codebase": {
      "command": "/Users/tuonome/Delta/venv/bin/python",
      "args": ["-m", "mcp_server"],
      "env": {
        "MCP_PROJECT_ROOT": "/Users/tuonome/progetti/mio-progetto"
      }
    }
  }
}
```

## Windows

```json
{
  "mcpServers": {
    "codebase": {
      "command": "C:\\Users\\TuoNome\\Delta\\venv\\Scripts\\python.exe",
      "args": ["-m", "mcp_server"],
      "env": {
        "MCP_PROJECT_ROOT": "C:\\Users\\TuoNome\\progetti\\mio-progetto"
      }
    }
  }
}
```

## Note Importanti

1. **Path assoluti:** Usa sempre path completi, non relativi
2. **Venv Python:** Punta al Python dentro il virtualenv, non quello di sistema
3. **Separatori:** Su Windows usa `\\` o `/`, su Mac/Linux usa `/`
4. **MCP_PROJECT_ROOT:** Percorso del progetto che vuoi analizzare
5. **Riavvio:** Riavvia Claude Desktop dopo ogni modifica del config

## Come Trovare il Path Python del Venv

### macOS/Linux
```bash
cd Delta
source venv/bin/activate
which python
# Copia questo path nel config
```

### Windows
```cmd
cd Delta
venv\Scripts\activate
where python
REM Copia questo path nel config
```

## Verifica Configurazione

1. Apri Claude Desktop
2. Controlla i log: Help → View Logs
3. Cerca righe tipo: "Connected to MCP server: codebase"
4. Se vedi errori, verifica i path nel config
