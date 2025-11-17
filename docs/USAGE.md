# Guida all'Uso

Esempi pratici di utilizzo del server MCP per l'analisi del codebase.

## Strumenti MCP Disponibili

### 1. list_files
Elenca tutti i file nel progetto.

**Esempio in Claude:**
```
Mostrami tutti i file Python nel progetto
```

Claude userà: `list_files(pattern="*.py")`

### 2. read_file
Legge il contenuto di un file specifico.

**Esempio:**
```
Mostrami il contenuto di mcp_server/server.py
```

### 3. get_indexed_files
Mostra i file indicizzati con riassunti.

**Esempio:**
```
Quali file sono stati indicizzati?
```

### 4. search_symbols
Cerca simboli (classi, funzioni) per nome.

**Esempi:**
```
Trova tutte le classi che contengono "Parser" nel nome
```
→ `search_symbols(query="Parser", kind="class")`

```
Cerca funzioni che si chiamano "handle_"
```
→ `search_symbols(query="handle_")`

### 5. get_file_symbols
Mostra la struttura di un file.

**Esempio:**
```
Mostrami la struttura del file mcp_server/database.py
```
→ `get_file_symbols(path="mcp_server/database.py")`

Output:
```
Struttura di mcp_server/database.py:

## Classes

- Database (linea 15)
  └─ Gestisce la connessione e le operazioni sul database SQLite.

## Functions

  - connect() (linea 28)
    └─ Apre la connessione al database.

  - close() (linea 34)
    └─ Chiude la connessione al database.
```

### 6. semantic_search
Ricerca semantica per contenuto.

**Esempi:**
```
Trova file che gestiscono autenticazione utenti
```
→ `semantic_search(query="authentication and user login", limit=10)`

```
Cerca codice relativo a database e SQL
```
→ `semantic_search(query="database queries and SQL operations")`

### 7. get_symbol_references
Trova referenze a un simbolo.

**Esempio:**
```
Dove viene chiamata la funzione Database?
```
→ `get_symbol_references(symbol_name="Database")`

### 8. lint_python
Analisi statica Python.

**Esempi:**
```
Analizza il codice Python per errori
```
→ `lint_python()`

```
Analizza e correggi automaticamente il file server.py
```
→ `lint_python(target="mcp_server/server.py", fix=true)`

### 9. lint_javascript
Analisi statica JavaScript/TypeScript.

**Esempio:**
```
Esegui ESLint sul progetto frontend
```
→ `lint_javascript(target="frontend/src")`

### 10. get_available_linters
Verifica strumenti disponibili.

**Esempio:**
```
Quali strumenti di linting sono installati?
```

## Casi d'Uso Completi

### Caso 1: Analisi di un Nuovo Progetto

**Scenario:** Hai appena clonato un repository e vuoi capire la struttura.

**Conversazione con Claude:**

```
User: Ho appena clonato questo progetto. Aiutami a capire cosa fa.

Claude: Certo! Iniziamo guardando la struttura.
→ [usa get_indexed_files]

Claude: Vedo che è un server MCP in Python. Ecco i file principali:
- server.py: Server MCP principale
- database.py: Gestione database
- indexer.py: Indicizzatore del codebase
...

User: Cosa fa esattamente il server?

Claude: Lasciami controllare la struttura del server.
→ [usa get_file_symbols su server.py]

Claude: Il server espone questi strumenti MCP:
- list_files: elenca file
- search_symbols: cerca nel codice
- semantic_search: ricerca semantica
...
```

### Caso 2: Trovare Bug

**Scenario:** C'è un bug nella gestione del database.

```
User: C'è un bug quando chiudo il database. Aiutami a trovarlo.

Claude: Cerchiamo la funzione close nel codice.
→ [usa search_symbols(query="close")]

Claude: Ho trovato Database.close() in database.py:34.
Lasciami leggere il file.
→ [usa read_file(path="mcp_server/database.py")]

Claude: Vedo il problema! La funzione close() non controlla se
self.db è già None prima di chiudere. Ecco la fix...
```

### Caso 3: Refactoring

**Scenario:** Vuoi rinominare una funzione.

```
User: Voglio rinominare calculate_hash in compute_file_hash.
      Dove viene usata?

Claude: Cerchiamo tutti i riferimenti.
→ [usa search_symbols(query="calculate_hash")]
→ [usa get_symbol_references(symbol_name="calculate_hash")]

Claude: La funzione è definita in server.py:69 e viene chiamata in:
- indexer.py:277
- indexer.py:335

Vuoi che ti mostri il codice di queste posizioni?
```

### Caso 4: Code Review

**Scenario:** Revisione del codice prima del commit.

```
User: Voglio fare un code review del modulo indexer.

Claude: Analizziamo il codice.
→ [usa lint_python(target="mcp_server/indexer.py")]

Claude: Ho trovato 3 problemi:

ERRORI (1):
- indexer.py:142:5 [mypy] error: Missing type annotation...

WARNINGS (2):
- indexer.py:89:0 [ruff] line too long (92 > 88 characters)
- indexer.py:156:0 [pylint] consider-using-with

Vuoi che ti spieghi come risolverli?
```

### Caso 5: Documentazione

**Scenario:** Generare documentazione per una classe.

```
User: Genera documentazione per la classe CodeParser.

Claude: Analizzo la struttura.
→ [usa search_symbols(query="CodeParser", kind="class")]
→ [usa get_file_symbols(path="mcp_server/parser.py")]

Claude: # CodeParser

Parser del codice usando tree-sitter.

## Metodi

### __init__(self)
Inizializza il parser con le grammatiche...

### parse_file(self, content: str, language: str)
Analizza un file e estrae simboli...
...
```

## Workflow Consigliati

### Workflow 1: Daily Development

1. **Mattina:** `get_indexed_files` per vedere cambiamenti
2. **Durante sviluppo:** `search_symbols` per trovare definizioni
3. **Prima del commit:** `lint_python` per controllo qualità
4. **Code review:** `get_file_symbols` per capire struttura

### Workflow 2: Debugging

1. `search_symbols` per trovare funzione problematica
2. `get_symbol_references` per vedere chi la chiama
3. `read_file` per leggere il contesto
4. Fix → `lint_python` per verificare

### Workflow 3: Onboarding

1. `get_indexed_files` per overview
2. `semantic_search` per trovare funzionalità specifiche
3. `get_file_symbols` per capire moduli principali
4. `read_file` per dettagli implementativi

## Tips & Tricks

### Ricerche Efficaci

**Cerca per pattern:**
```
Trova tutte le funzioni async
→ search_symbols(query="async_")
```

**Ricerca semantica in linguaggio naturale:**
```
File che gestiscono errori e eccezioni
→ semantic_search(query="error handling and exception management")
```

### Analisi Incrementale

**Analizza solo file modificati:**
```bash
# In CLI
git diff --name-only | grep "\.py$" > changed_files.txt

# Poi in Claude
Analizza questi file: [incolla lista]
```

### Automazione

**Crea alias per comandi comuni:**
```bash
# In .bashrc o .zshrc
alias mcp-index='python -m mcp_server.cli index'
alias mcp-stats='python -m mcp_server.cli stats'
alias mcp-lint='python -m mcp_server.cli lint'  # se implementato
```

## Limitazioni

- **File grandi:** File >1MB non vengono indicizzati
- **File binari:** Solo file di testo supportati
- **Linguaggi:** Parsing completo solo per 9 linguaggi
- **Performance:** Ricerca semantica può essere lenta su progetti molto grandi

## Prossimi Passi

- Consulta [API.md](API.md) per dettagli tecnici
- Vedi [EXAMPLES.md](EXAMPLES.md) per scenari avanzati
- Contribuisci su [GitHub](repository-url)
