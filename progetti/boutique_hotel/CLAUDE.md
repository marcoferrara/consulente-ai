# Boutique Hotel Antiga Luna — CLAUDE.md

## Progetto
Chatbot AI per boutique hotel. Backend FastAPI con supporto OpenAI e Gemini (fallback automatico). Gestisce prenotazioni dirette, info camere, e incentivi booking diretto.

## Stack
- **Backend:** Python, FastAPI, Uvicorn
- **AI:** OpenAI (primario) + Google Gemini (fallback)
- **Config:** `config.py` (dati camere, nome hotel, benefici)
- **Test:** `test_client.py`

## Struttura
```
app.py          # Server principale FastAPI
config.py       # ROOMS_DB, HOTEL_NAME, chiavi API
index.html      # Frontend chatbot
static/         # Asset statici
requirements.txt
test_client.py  # Script di test manuale
```

## Comandi
```bash
pip install -r requirements.txt
uvicorn app:app --reload    # Dev server (localhost:8000)
python test_client.py       # Test manuale endpoint
```

## Variabili d'ambiente (.env o config.py)
```
GEMINI_API_KEY=...
OPENAI_API_KEY=...
```

## Convenzioni
- Commenti in italiano su ogni funzione
- Indentazione 4 spazi (PEP8)
- Conventional commits in italiano
