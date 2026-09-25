# Cantina Vinicola — CLAUDE.md

## Progetto
Chatbot AI per cantina vinicola sarda. Backend FastAPI con Gemini. Gestisce info vini, prenotazioni degustazioni, acquisti.

## Stack
- **Backend:** Python, FastAPI
- **AI:** Google Gemini
- **Config:** `config.py` (nome cantina, chiavi API, porta)
- **Storage:** JSON locale (`database.json`)

## Struttura
```
app.py          # Server principale FastAPI
config.py       # GEMINI_API_KEY, WINERY_NAME, WINERY_BIO, PORT
database.json   # Catalogo vini e dati cantina
index.html      # Frontend chatbot
requirements.txt
```

## Comandi
```bash
pip install -r requirements.txt
uvicorn app:app --reload    # Dev server
```

## Variabili d'ambiente (.env o config.py)
```
GEMINI_API_KEY=...
```

## Convenzioni
- Commenti in italiano su ogni funzione
- Indentazione 4 spazi (PEP8)
- Conventional commits in italiano
