# SardiniaLogistics AI — CLAUDE.md

## Progetto
API di ottimizzazione logistica e rotte montane per la Sardegna. Backend FastAPI con database rotte simulato ad alta fedeltà.

## Stack
- **Backend:** Python, FastAPI, Uvicorn
- **Storage:** Dati rotte hardcoded in `app.py` (simulazione)
- **Frontend:** `index.html` + asset statici

## Struttura
```
app.py          # Server FastAPI — logica rotte e ottimizzazione
index.html      # Frontend dashboard logistica
requirements.txt
```

## Comandi
```bash
pip install -r requirements.txt
uvicorn app:app --reload    # Dev server (localhost:8000)
```

## Convenzioni
- Commenti in italiano su ogni funzione
- Indentazione 4 spazi (PEP8)
- Conventional commits in italiano
