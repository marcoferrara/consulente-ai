# Social Pesca — CLAUDE.md

## Progetto
Piattaforma AI per la community della pesca sportiva in Sardegna. Backend FastAPI con Gemini. Gestisce bandi regionali, contenuti social, upload foto e deploy su Render/Docker.

## Stack
- **Backend:** Python, FastAPI, Uvicorn
- **AI:** Google Gemini (`google-genai`)
- **Deploy:** Render (`Dockerfile`)
- **Storage:** JSON locale (`database.json`)

## Struttura
```
app.py              # Server principale FastAPI
index.html          # Frontend principale
bandi.html          # Pagina bandi regionali pesca
database.json       # Dati community e contenuti
gdd_light.md        # Game Design Document leggero
requirements.txt
Dockerfile
uploads/            # Foto caricate dagli utenti
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
