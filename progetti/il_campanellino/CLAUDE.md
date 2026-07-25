# Il Campanellino — CLAUDE.md

## Progetto
Landing page con backend FastAPI per raccolta lead. Cliente: agenzia eventi e spettacolo "Il Campanellino". I contatti dei clienti vengono salvati in `leads.json`.

## Stack
- **Backend:** Python, FastAPI, Uvicorn
- **Storage:** JSON locale (`leads.json`)
- **Frontend:** HTML statico (`index.html`, `index_v2.html`)

## Struttura
```
app.py          # Server FastAPI — gestisce form contatti → leads.json
index.html      # Landing page v1
index_v2.html   # Landing page v2 (versione aggiornata)
leads.json      # Database contatti raccolti
```

## Comandi
```bash
pip install fastapi uvicorn
uvicorn app:app --reload    # Dev server (localhost:8000)
```

## Note
- Nessuna dipendenza AI — è un semplice backend per raccolta lead
- `index_v2.html` è la versione più recente da usare come riferimento

## Convenzioni
- Commenti in italiano su ogni funzione
- Indentazione 4 spazi (PEP8)
- Conventional commits in italiano
