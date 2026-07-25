# Ricambi Truck — CLAUDE.md

## Progetto
Due moduli distinti nello stesso progetto:
1. **Bot telefonico** (`app.py`, porta 8000): riceve chiamate da Vapi.ai, estrae dati con Gemini, notifica su WhatsApp
2. **Agente RDP** (`agent_app.py`, porta 8001): dato un telaio + lista ricambi, si connette al desktop remoto Windows via RDP, naviga i software EPC dei costruttori truck e restituisce i codici originali + screenshot annotati

## Stack

### Bot telefonico (esistente)
- **Backend:** Python, FastAPI
- **AI:** Google Gemini 2.5 Flash
- **Storage:** JSON locale (`calls.json`)

### Agente RDP (nuovo)
- **Backend:** Python, FastAPI
- **AI:** Claude API `claude-opus-4-8` con Computer Use
- **RDP:** `mstsc.exe` + `pyautogui` + `pywin32`
- **Immagini:** Pillow + OpenCV
- **Knowledge Base:** YAML per marchio (in `knowledge_base/`)
- **Storage:** JSON locale (`ricerche.json`)

## Struttura
```
app.py                    # Bot telefonico (non modificare)
agent_app.py              # Server agente RDP — porta 8001
agent/
  __init__.py
  orchestrator.py         # Coordinatore principale
  vin_decoder.py          # Identifica marchio da telaio VIN
  rdp_controller.py       # Gestione sessione RDP
  computer_use.py         # Loop Claude API computer use
  image_annotator.py      # Cerchio rosso su screenshot
  notifier.py             # WhatsApp report
knowledge_base/
  iveco.yaml              # Guida navigazione IVECO EPC ← COMPILARE CON CLIENTE
  scania.yaml             # DA COMPILARE
  man.yaml                # DA COMPILARE
  daf.yaml                # DA COMPILARE
  volvo.yaml              # DA COMPILARE
  renault.yaml            # DA COMPILARE
  mercedes.yaml           # DA COMPILARE
screenshots/              # Screenshot annotati (auto-generata)
calls.json                # Log chiamate bot telefonico
ricerche.json             # Log ricerche agente RDP
requirements.txt          # Dipendenze bot telefonico
requirements_agent.txt    # Dipendenze agente RDP
```

## Comandi

```bash
# Bot telefonico (porta 8000)
pip install -r requirements.txt
uvicorn app:app --reload

# Agente RDP (porta 8001)
pip install -r requirements_agent.txt
uvicorn agent_app:app --port 8001 --reload

# Test VIN decoder
python -m agent.vin_decoder

# Test rapido RDP (senza computer use)
python -c "from agent.rdp_controller import RDPController; rdp = RDPController(); rdp.apri_sessione()"
```

## Variabili d'ambiente (.env)
```
GEMINI_API_KEY=...              # Bot telefonico
ANTHROPIC_API_KEY=...           # Agente RDP (computer use)
RDP_HOST=...                    # IP server desktop remoto
RDP_PORT=3389
RDP_USER=...
RDP_PASSWORD=...
COMPANY_DESTINATION_NUMBER=...  # Numero WhatsApp destinatario
CALLMEBOT_API_KEY=...
WHATSAPP_GATEWAY_URL=           # Opzionale, per invio immagini
WHATSAPP_INSTANCE_ID=
WHATSAPP_TOKEN=
```

## Knowledge Base — Come compilare
I file YAML in `knowledge_base/` guidano Claude nella navigazione del software EPC.
**Da compilare insieme al cliente** durante sessioni registrate di utilizzo reale:
1. Aprire il software EPC del marchio
2. Eseguire una ricerca reale registrando ogni passo
3. Aggiungere i passi nel file YAML del marchio
4. Documentare particolarità (modelli, versioni Euro, sezioni non ovvie)

Il file `iveco.yaml` ha la struttura completa come riferimento.

## Flusso agente RDP
```
Form web (telaio + ricambi)
  ↓
VIN Decoder → identifica marchio
  ↓
Carica knowledge_base/<marchio>.yaml
  ↓
RDP Controller → apre sessione mstsc.exe
  ↓
Computer Use Agent (Claude) → naviga EPC, trova codici
  ↓
Image Annotator → cerchio rosso sullo screenshot
  ↓
Notifier → messaggio WhatsApp + screenshot
```

## Convenzioni
- Commenti in italiano su ogni funzione
- Indentazione 4 spazi (PEP8)
- Conventional commits in italiano
- Mai committare credenziali (.env ignorato da git)
