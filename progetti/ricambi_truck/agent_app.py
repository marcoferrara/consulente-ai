# agent_app.py
# Server FastAPI per l'agente di ricerca ricambi truck — porta 8001
# Interfaccia web per input manuale (telaio + lista ricambi) e monitoraggio ricerche

import os
import sys
import json
import uuid
import logging
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Fix encoding UTF-8 su Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RICERCHE_FILE = os.path.join(BASE_DIR, "ricerche.json")

# Inizializza il file storico ricerche se non esiste
if not os.path.exists(RICERCHE_FILE):
    with open(RICERCHE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

app = FastAPI(title="Agente Ricerca Ricambi Truck")


# --- Modelli dati ---

class RicercaRequest(BaseModel):
    telaio: str
    ricambi: list[str]
    cliente: Optional[str] = None
    note: Optional[str] = None


class RicercaStatus(BaseModel):
    id: str
    telaio: str
    marchio: Optional[str]
    ricambi: list[str]
    cliente: Optional[str]
    stato: str  # "in_coda" | "in_corso" | "completata" | "errore"
    risultati: Optional[list[dict]] = None
    messaggio_finale: Optional[str] = None
    errore: Optional[str] = None
    creata_at: str
    completata_at: Optional[str] = None


# --- Storage ricerche ---

def load_ricerche() -> list[dict]:
    try:
        with open(RICERCHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_ricerca(ricerca: dict) -> None:
    ricerche = load_ricerche()
    # Aggiorna se esiste già, altrimenti inserisce in testa
    for i, r in enumerate(ricerche):
        if r["id"] == ricerca["id"]:
            ricerche[i] = ricerca
            break
    else:
        ricerche.insert(0, ricerca)
    # Conserva le ultime 100 ricerche
    with open(RICERCHE_FILE, "w", encoding="utf-8") as f:
        json.dump(ricerche[:100], f, indent=2, ensure_ascii=False)


# --- Task background per la ricerca ---

async def esegui_ricerca(ricerca_id: str) -> None:
    """
    Avvia l'orchestratore dell'agente in background per una ricerca specifica.
    Aggiorna lo stato nel file JSON durante l'esecuzione.
    """
    ricerche = load_ricerche()
    ricerca = next((r for r in ricerche if r["id"] == ricerca_id), None)
    if not ricerca:
        logger.error(f"Ricerca {ricerca_id} non trovata")
        return

    try:
        ricerca["stato"] = "in_corso"
        save_ricerca(ricerca)

        # Import lazy per evitare errori di import al boot se le dipendenze mancano
        from agent.orchestrator import OrchestratoreRicerca
        orchestratore = OrchestratoreRicerca()
        risultati, messaggio = await orchestratore.esegui(
            telaio=ricerca["telaio"],
            ricambi=ricerca["ricambi"],
            marchio=ricerca["marchio"],
        )
        ricerca["stato"] = "completata"
        ricerca["risultati"] = risultati
        ricerca["messaggio_finale"] = messaggio
        ricerca["completata_at"] = datetime.now().isoformat()

    except Exception as e:
        logger.error(f"Errore nella ricerca {ricerca_id}: {e}", exc_info=True)
        ricerca["stato"] = "errore"
        ricerca["errore"] = str(e)
        ricerca["completata_at"] = datetime.now().isoformat()

    save_ricerca(ricerca)


# --- API Endpoints ---

@app.post("/api/ricerca", response_model=dict)
async def avvia_ricerca(req: RicercaRequest, background_tasks: BackgroundTasks):
    """Avvia una nuova ricerca ricambi in background."""
    from agent.vin_decoder import decode_vin

    # Pulizia input
    telaio = req.telaio.strip().upper()
    ricambi = [r.strip() for r in req.ricambi if r.strip()]

    if not telaio:
        raise HTTPException(status_code=400, detail="Telaio obbligatorio")
    if not ricambi:
        raise HTTPException(status_code=400, detail="Lista ricambi obbligatoria")

    marchio = decode_vin(telaio)

    ricerca: dict = {
        "id": str(uuid.uuid4())[:8],
        "telaio": telaio,
        "marchio": marchio,
        "ricambi": ricambi,
        "cliente": req.cliente,
        "note": req.note,
        "stato": "in_coda",
        "risultati": None,
        "messaggio_finale": None,
        "errore": None,
        "creata_at": datetime.now().isoformat(),
        "completata_at": None,
    }
    save_ricerca(ricerca)

    if not marchio:
        ricerca["stato"] = "errore"
        ricerca["errore"] = f"Marchio non riconosciuto per telaio '{telaio}'. Prefisso WMI sconosciuto."
        save_ricerca(ricerca)
        return {"id": ricerca["id"], "stato": ricerca["stato"], "errore": ricerca["errore"]}

    background_tasks.add_task(esegui_ricerca, ricerca["id"])

    logger.info(f"Ricerca {ricerca['id']} avviata — Marchio: {marchio}, Ricambi: {ricambi}")
    return {"id": ricerca["id"], "marchio": marchio, "stato": "in_coda"}


@app.get("/api/ricerca/{ricerca_id}")
async def stato_ricerca(ricerca_id: str):
    """Restituisce lo stato e i risultati di una ricerca."""
    ricerche = load_ricerche()
    ricerca = next((r for r in ricerche if r["id"] == ricerca_id), None)
    if not ricerca:
        raise HTTPException(status_code=404, detail="Ricerca non trovata")
    return JSONResponse(content=ricerca)


@app.get("/api/ricerche")
async def lista_ricerche():
    """Restituisce lo storico di tutte le ricerche."""
    return JSONResponse(content=load_ricerche())


# --- Dashboard web ---

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Interfaccia web principale per inserimento e monitoraggio ricerche."""
    html = """<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Agente Ricerca Ricambi Truck</title>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;500;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0F172A;
      --card: #1E293B;
      --border: #334155;
      --text: #F8FAFC;
      --muted: #94A3B8;
      --blue: #3B82F6;
      --blue-dark: #1E3A8A;
      --yellow: #F59E0B;
      --green: #10B981;
      --red: #EF4444;
      --radius: 14px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); padding-bottom: 60px; }
    header {
      background: linear-gradient(135deg, #1E3B8B 0%, #0F172A 100%);
      padding: 20px 40px;
      border-bottom: 1px solid var(--border);
      display: flex; align-items: center; gap: 16px;
    }
    header h1 { font-family: 'Outfit', sans-serif; font-size: 24px; font-weight: 800; }
    header h1 span { color: var(--yellow); }
    .container { max-width: 1100px; margin: 30px auto; padding: 0 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
    @media (max-width: 800px) { .container { grid-template-columns: 1fr; } }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; }
    .card h2 { font-family: 'Outfit', sans-serif; font-size: 18px; font-weight: 600; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 8px; }
    .form-group { margin-bottom: 16px; }
    .form-group label { display: block; font-size: 11px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
    .form-group input, .form-group textarea {
      width: 100%; background: #0F172A; border: 1.5px solid var(--border);
      border-radius: 8px; color: var(--text); padding: 10px 12px; font-size: 14px;
      outline: none; font-family: 'Inter', sans-serif; transition: border-color 0.2s;
    }
    .form-group textarea { height: 120px; resize: vertical; }
    .form-group input:focus, .form-group textarea:focus { border-color: var(--blue); }
    .btn {
      background: linear-gradient(135deg, var(--blue) 0%, var(--blue-dark) 100%);
      color: #fff; border: none; border-radius: 8px; padding: 12px 20px;
      font-size: 14px; font-weight: 700; cursor: pointer; width: 100%;
      box-shadow: 0 4px 15px rgba(59,130,246,0.3); transition: opacity 0.2s;
    }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .hint { font-size: 12px; color: var(--muted); margin-top: 4px; }
    .ricerche-list { display: flex; flex-direction: column; gap: 12px; max-height: 680px; overflow-y: auto; }
    .ricerca-item { background: #0F172A; border: 1px solid var(--border); border-radius: 10px; padding: 14px; }
    .ricerca-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
    .ricerca-id { font-size: 12px; color: var(--muted); font-family: monospace; }
    .badge { font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px; text-transform: uppercase; }
    .badge.in_coda { background: rgba(245,158,11,0.15); color: var(--yellow); border: 1px solid var(--yellow); }
    .badge.in_corso { background: rgba(59,130,246,0.15); color: var(--blue); border: 1px solid var(--blue); }
    .badge.completata { background: rgba(16,185,129,0.15); color: var(--green); border: 1px solid var(--green); }
    .badge.errore { background: rgba(239,68,68,0.15); color: var(--red); border: 1px solid var(--red); }
    .ricerca-telaio { font-weight: 700; color: var(--yellow); font-family: monospace; }
    .ricerca-marchio { font-size: 13px; color: var(--blue); font-weight: 600; }
    .ricambi-list { font-size: 13px; color: var(--muted); margin-top: 6px; }
    .risultati-box { background: #1a2332; border-radius: 8px; padding: 12px; margin-top: 10px; font-size: 13px; white-space: pre-wrap; font-family: monospace; color: var(--text); border-left: 3px solid var(--green); }
    .errore-box { background: rgba(239,68,68,0.08); border-radius: 8px; padding: 12px; margin-top: 10px; font-size: 13px; color: var(--red); border-left: 3px solid var(--red); }
    .empty-state { text-align: center; padding: 40px 20px; color: var(--muted); }
  </style>
</head>
<body>
  <header>
    <div>🚛</div>
    <h1>Agente Ricerca Ricambi <span>Truck</span></h1>
  </header>

  <div class="container">
    <!-- Form inserimento ricerca -->
    <div class="card">
      <h2>🔍 Nuova Ricerca</h2>

      <div class="form-group">
        <label>Telaio / VIN</label>
        <input type="text" id="telaio" placeholder="es. ZFA6H0000S1234567" style="text-transform:uppercase">
        <div class="hint" id="marchio-hint"></div>
      </div>

      <div class="form-group">
        <label>Cliente (opzionale)</label>
        <input type="text" id="cliente" placeholder="es. Officina Rossi - Mario">
      </div>

      <div class="form-group">
        <label>Ricambi richiesti (uno per riga)</label>
        <textarea id="ricambi" placeholder="filtro olio motore&#10;pastiglie freno anteriori&#10;alternatore 24V"></textarea>
      </div>

      <div class="form-group">
        <label>Note aggiuntive (opzionale)</label>
        <input type="text" id="note" placeholder="es. urgenza, preferenze, ecc.">
      </div>

      <button class="btn" id="btn-avvia" onclick="avviaRicerca()">🚀 Avvia Ricerca Automatica</button>
    </div>

    <!-- Storico ricerche -->
    <div class="card">
      <h2>📋 Ricerche in Corso / Storico</h2>
      <div class="ricerche-list" id="ricerche-list">
        <div class="empty-state">Nessuna ricerca ancora. Compila il form a sinistra!</div>
      </div>
    </div>
  </div>

  <script>
    // Decodifica marchio in tempo reale mentre si digita il telaio
    const WMI_MAP = {
      'ZFA':'IVECO','ZCF':'IVECO','ZFF':'IVECO','ZGB':'IVECO','ZGT':'IVECO','ZLA':'IVECO',
      'YS2':'SCANIA','YS3':'SCANIA',
      'WMA':'MAN','WMN':'MAN','WMK':'MAN',
      'XLR':'DAF','XLD':'DAF','XLB':'DAF','XLF':'DAF',
      'YV2':'VOLVO','YV1':'VOLVO','YV3':'VOLVO',
      'VF6':'RENAULT','VF3':'RENAULT',
      'WDB':'MERCEDES','WDC':'MERCEDES','WDD':'MERCEDES','WEB':'MERCEDES',
    };

    document.getElementById('telaio').addEventListener('input', function() {
      const val = this.value.toUpperCase().replace(/\\s/g,'');
      this.value = val;
      const wmi = val.substring(0, 3);
      const hint = document.getElementById('marchio-hint');
      if (wmi.length >= 3) {
        const marchio = WMI_MAP[wmi];
        hint.textContent = marchio ? `✅ Marchio rilevato: ${marchio}` : '⚠️ Prefisso WMI non riconosciuto — verificare il telaio';
        hint.style.color = marchio ? '#10B981' : '#F59E0B';
      } else {
        hint.textContent = '';
      }
    });

    async function avviaRicerca() {
      const telaio = document.getElementById('telaio').value.trim();
      const cliente = document.getElementById('cliente').value.trim();
      const ricambiTxt = document.getElementById('ricambi').value.trim();
      const note = document.getElementById('note').value.trim();

      if (!telaio || !ricambiTxt) {
        alert('Inserisci telaio e almeno un ricambio prima di procedere.');
        return;
      }

      const ricambi = ricambiTxt.split('\\n').map(r => r.trim()).filter(r => r);
      const btn = document.getElementById('btn-avvia');
      btn.disabled = true;
      btn.textContent = 'Avvio in corso...';

      try {
        const resp = await fetch('/api/ricerca', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({telaio, ricambi, cliente: cliente||null, note: note||null})
        });
        const data = await resp.json();

        if (data.errore) {
          alert('Errore: ' + data.errore);
        } else {
          alert(`Ricerca avviata! ID: ${data.id} — Marchio: ${data.marchio}\\nMonitora il pannello a destra.`);
          fetchRicerche();
          // Polling automatico ogni 5 secondi
          const poller = setInterval(async () => {
            const r = await fetch('/api/ricerca/' + data.id);
            const rd = await r.json();
            if (rd.stato === 'completata' || rd.stato === 'errore') {
              clearInterval(poller);
              fetchRicerche();
            }
          }, 5000);
        }
      } catch(e) {
        alert('Errore di connessione: ' + e.message);
      } finally {
        btn.disabled = false;
        btn.textContent = '🚀 Avvia Ricerca Automatica';
      }
    }

    async function fetchRicerche() {
      const resp = await fetch('/api/ricerche');
      const ricerche = await resp.json();
      const container = document.getElementById('ricerche-list');

      if (!ricerche.length) {
        container.innerHTML = '<div class="empty-state">Nessuna ricerca ancora. Compila il form a sinistra!</div>';
        return;
      }

      container.innerHTML = ricerche.map(r => {
        const ricambiHtml = r.ricambi.map(rc => `• ${rc}`).join('<br>');
        let extraHtml = '';
        if (r.messaggio_finale) {
          extraHtml = `<div class="risultati-box">${escHtml(r.messaggio_finale)}</div>`;
        } else if (r.errore) {
          extraHtml = `<div class="errore-box">❌ ${escHtml(r.errore)}</div>`;
        }
        return `
          <div class="ricerca-item">
            <div class="ricerca-header">
              <div>
                <span class="ricerca-id">#${r.id}</span>
                ${r.cliente ? `<span style="font-size:12px;color:#94A3B8;margin-left:8px">${escHtml(r.cliente)}</span>` : ''}
              </div>
              <span class="badge ${r.stato}">${r.stato.replace('_',' ')}</span>
            </div>
            <div class="ricerca-telaio">${escHtml(r.telaio)}</div>
            ${r.marchio ? `<div class="ricerca-marchio">🏷️ ${r.marchio}</div>` : ''}
            <div class="ricambi-list">${ricambiHtml}</div>
            ${extraHtml}
          </div>`;
      }).join('');
    }

    function escHtml(str) {
      return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }

    // Carica storico all'avvio e poi ogni 10 secondi
    fetchRicerche();
    setInterval(fetchRicerche, 10000);
  </script>
</body>
</html>"""
    return HTMLResponse(content=html)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agent_app:app", host="127.0.0.1", port=8001, reload=True)
