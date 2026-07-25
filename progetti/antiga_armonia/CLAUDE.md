# Antiga Armonia — CLAUDE.md

## Progetto
Chatbot AI per agriturismo sardo. Backend FastAPI con Google Gemini. Gestisce prenotazioni, info struttura, upload immagini e automazione social media. Deployato su Render.

## Stack
- **Backend:** Python, FastAPI, Uvicorn
- **AI:** Google Gemini (`google-generativeai`)
- **Deploy:** Render (`render.yaml` + `Dockerfile`)
- **Storage:** JSON locale (`database.json`)

## Struttura
```
app.py                      # Server principale FastAPI
index.html                  # Frontend chatbot
database.json               # Dati struttura (camere, servizi, ecc.)
requirements.txt
render.yaml                 # Config deploy Render
Dockerfile
social_media_automation/    # Automazione post social
voice_calling_bot/          # Bot chiamate vocali
uploads/                    # Immagini caricate
```

## Comandi
```bash
pip install -r requirements.txt
uvicorn app:app --reload    # Dev server (localhost:8000)
```

## Variabili d'ambiente (.env)
```
GEMINI_API_KEY=...
```

## Convenzioni
- Commenti in italiano su ogni funzione
- Indentazione 4 spazi (PEP8)
- Conventional commits in italiano
