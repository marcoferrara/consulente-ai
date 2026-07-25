# Studio Associato — RAG AI Engine — CLAUDE.md

## Progetto
Backend RAG (Retrieval-Augmented Generation) per uno studio associato. Motore di corrispondenza semantica tra bandi regionali e aziende clienti. Aiuta i consulenti a trovare i bandi più adatti per ogni cliente.

## Stack
- **Backend:** Python, FastAPI, Uvicorn
- **Config:** `config.py` (AZIENDE_DB, BANDI_DB, PORT)

## Struttura
```
app.py          # Server FastAPI — motore RAG matching bandi/aziende
config.py       # Database aziende, database bandi, configurazione porta
index.html      # Frontend interfaccia consulenti
requirements.txt
```

## Comandi
```bash
pip install -r requirements.txt
uvicorn app:app --reload    # Dev server
```

## Logica core
- `AZIENDE_DB` in `config.py` — profili aziende clienti
- `BANDI_DB` in `config.py` — catalogo bandi regionali
- L'API trova corrispondenze semantiche tra le due liste

## Convenzioni
- Commenti in italiano su ogni funzione
- Indentazione 4 spazi (PEP8)
- Conventional commits in italiano
