import os
import json
import logging
from typing import Dict, Any, List
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import httpx

# Inizializzazione Logger e Variabili d'Ambiente
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Carica variabili da .env locale
load_dotenv()

# Configura Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Gemini API configurata con successo.")
else:
    logger.warning("ATTENZIONE: GEMINI_API_KEY non trovata nel file .env!")

app = FastAPI(title="Truck AI Phone Responder")

DB_FILE = "calls.json"

# Inizializza il file calls.json se non esiste
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

# Modello dati per la simulazione
class SimulationRequest(BaseModel):
    transcript: str
    customer_phone: str = "+39 347 1234567"
    recording_url: str = "https://api.vapi.ai/recordings/dummy-truck-call.mp3"

def load_calls() -> List[Dict[str, Any]]:
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Errore nel caricamento del database chiamate: {e}")
        return []

def save_call(call_data: Dict[str, Any]):
    try:
        calls = load_calls()
        calls.insert(0, call_data)  # Aggiungi in testa (più recente)
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(calls[:50], f, indent=2, ensure_ascii=False) # Conserva le ultime 50 chiamate
    except Exception as e:
        logger.error(f"Errore nel salvataggio della chiamata: {e}")

async def send_to_whatsapp(report_text: str, audio_url: str) -> bool:
    """
    Funzione per l'invio del report a WhatsApp tramite Gateway Flat.
    Configurabile tramite variabili .env
    """
    gateway_url = os.getenv("WHATSAPP_GATEWAY_URL")
    instance_id = os.getenv("WHATSAPP_INSTANCE_ID")
    token = os.getenv("WHATSAPP_TOKEN")
    dest_number = os.getenv("COMPANY_DESTINATION_NUMBER")

    if not all([gateway_url, dest_number]):
        logger.info("[WhatsApp Simulator] Credenziali non complete. Invio WhatsApp simulato nei log.")
        return False

    try:
        async with httpx.AsyncClient() as client:
            # Invio del Messaggio di Testo Report
            # Adatta i parametri in base alle specifiche di Z-API o Evolution API
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            payload = {
                "number": dest_number,
                "message": report_text
            }
            # Endpoint tipico per testo
            send_text_url = f"{gateway_url.rstrip('/')}/send-text"
            if instance_id:
                # Esempio Evolution API o Z-API
                send_text_url = f"{gateway_url.rstrip('/')}/message/sendText/{instance_id}"
            
            response = await client.post(send_text_url, json=payload, headers=headers, timeout=10.0)
            logger.info(f"WhatsApp Text Response: {response.status_code} - {response.text}")

            # Invio del File Audio Registrazione (se presente)
            if audio_url:
                send_audio_url = f"{gateway_url.rstrip('/')}/send-audio"
                if instance_id:
                    send_audio_url = f"{gateway_url.rstrip('/')}/message/sendAudio/{instance_id}"
                
                audio_payload = {
                    "number": dest_number,
                    "audio": audio_url
                }
                audio_response = await client.post(send_audio_url, json=audio_payload, headers=headers, timeout=10.0)
                logger.info(f"WhatsApp Audio Response: {audio_response.status_code}")

            return response.status_code in [200, 201]
    except Exception as e:
        logger.error(f"Errore durante l'invio WhatsApp reale: {e}")
        return False

def parse_transcript_with_gemini(transcript: str) -> Dict[str, Any]:
    """
    Usa Gemini 1.5 Flash per estrarre informazioni strutturate ed eseguire il parsing della targa lettera per lettera.
    """
    if not GEMINI_API_KEY:
        # Fallback offline mockup se non c'è chiave API per evitare crash
        return {
            "cliente": "Estratto Offline (Inserisci GEMINI_API_KEY)",
            "targa_telaio_grezza": "Non elaborata",
            "targa_telaio_ricostruita": "OFFLINE",
            "ricambi_richiesti": ["Aggiungi GEMINI_API_KEY in .env per elaborare"],
            "urgenza": "NORMALE",
            "sintesi": "Chiamata simulata senza elaborazione AI attiva."
        }

    # Prompt ottimizzato per il settore Truck e per la scanditura della targa con città
    prompt = f"""
Sei l'analista tecnico senior di Ricambi Truck Ferrara. Il tuo compito è analizzare la trascrizione di una telefonata e compilare un JSON strutturato contenente le informazioni chiave per il team di officina.

Presta particolare attenzione alla targa del veicolo. I clienti spesso scandiscono la targa lettera per lettera usando i nomi delle città (es. "Milano Torino due tre quattro Como Domodossola"). Reindirizza queste informazioni ricreando la targa italiana originale in stampatello maiuscolo (es. "MT234CD").
Ad esempio:
- Milano, Roma, Napoli, Torino, Firenze, Bologna, Ancona, Como, Domodossola, Palermo, Venezia, Genova, ecc. corrispondono alle loro rispettive lettere iniziali (M, R, N, T, F, B, A, C, D, P, V, G, ecc.).
- Se dicono "due tre quattro" scrivi "234".

Estrai un oggetto JSON con ESATTAMENTE le seguenti chiavi (e nessun altro testo di contorno):
{{
  "cliente": "Nome della persona ed eventuale officina o azienda (es. Mario Rossi - Officina Estense)",
  "targa_telaio_grezza": "Il testo esatto pronunciato dal cliente per la targa o il telaio",
  "targa_telaio_ricostruita": "La targa o il telaio ricostruito in maiuscolo e senza spazi (es. AB123CD)",
  "ricambi_richiesti": ["Lista dei pezzi di ricambio richiesti, es: Soffione sospensione, Alternatore 24V"],
  "urgenza": "Livello di urgenza. Deve essere SOLO uno tra: 'ALTA (Veicolo Fermo)' o 'NORMALE'",
  "sintesi": "Una singola frase sintetica ed efficace che descrive la richiesta del cliente"
}}

Trascrizione della chiamata:
\"\"\"
{transcript}
\"\"\"
"""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        parsed_json = json.loads(response.text.strip())
        return parsed_json
    except Exception as e:
        logger.error(f"Errore durante il parsing con Gemini: {e}")
        # In caso di errore restituiamo una struttura minima
        return {
            "cliente": "Errore Parsing Chiamata",
            "targa_telaio_grezza": "Non estratta",
            "targa_telaio_ricostruita": "ERRORE",
            "ricambi_richiesti": ["Errore elaborazione"],
            "urgenza": "NORMALE",
            "sintesi": f"Si è verificato un errore nell'elaborazione del testo: {str(e)}"
        }

def format_whatsapp_report(data: Dict[str, Any], phone: str, recording_url: str) -> str:
    """
    Formatta il report strutturato con emoticons accattivanti per la lettura aziendale su WhatsApp.
    """
    ricambi_str = "\n".join([f"  • _{r}_" for r in data.get("ricambi_richiesti", [])])
    
    report = (
        f"🚨 *NUOVA RICHIESTA TRUCK AI* 🚨\n\n"
        f"👤 *Cliente:* {data.get('cliente', 'Non specificato')}\n"
        f"📞 *Telefono:* {phone}\n\n"
        f"🚚 *Targa/Telaio:* `{data.get('targa_telaio_ricostruita', 'Non specificato')}`\n"
        f"🗣️ _Dettato come: \"{data.get('targa_telaio_grezza', '-')}\"_\n\n"
        f"🛠️ *Ricambi Richiesti:*\n{ricambi_str}\n\n"
        f"⚠️ *Urgenza:* {data.get('urgenza', 'NORMALE')}\n\n"
        f"📝 *Sintesi Assistente:* {data.get('sintesi', '-')}\n\n"
        f"🎧 *Registrazione Audio:* {recording_url}\n\n"
        f"👉 _Rispondi a questa notifica per avviare la chat con il cliente o chiamalo al numero sopra._"
    )
    return report

# --- API ENDPOINTS ---

@app.post("/webhook")
async def vapi_webhook(request: Request):
    """
    Endpoint per ricevere i Webhook reali di fine chiamata da Vapi.ai
    """
    try:
        body = await request.json()
        logger.info(f"Webhook ricevuto: {body.get('type')}")
        
        # Gestiamo solo il report finale di fine chiamata
        if body.get("type") == "end-of-call-report":
            call = body.get("call", {})
            transcript = body.get("transcript", "")
            recording_url = body.get("recordingUrl", "Nessuna registrazione")
            customer_phone = call.get("customer", {}).get("number", "Sconosciuto")
            
            if not transcript:
                logger.warning("Trascrizione vuota. Webhook ignorato.")
                return {"status": "ignored", "reason": "empty_transcript"}

            # 1. Analizza la trascrizione con Gemini
            ai_data = parse_transcript_with_gemini(transcript)
            
            # 2. Formatta il report WhatsApp
            report_text = format_whatsapp_report(ai_data, customer_phone, recording_url)
            
            # 3. Salva la chiamata nello storico locale
            call_record = {
                "id": call.get("id", "real-call"),
                "phone": customer_phone,
                "transcript": transcript,
                "recording_url": recording_url,
                "ai_data": ai_data,
                "report_text": report_text,
                "type": "reale"
            }
            save_call(call_record)
            
            # 4. Spedisci il messaggio WhatsApp reale (se configurato)
            whatsapp_status = await send_to_whatsapp(report_text, recording_url)
            
            return {
                "status": "success",
                "call_id": call.get("id"),
                "parsed_data": ai_data,
                "whatsapp_sent": whatsapp_status
            }
            
        return {"status": "ok", "message": "type_not_handled"}
    except Exception as e:
        logger.error(f"Errore nella gestione del webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simulate")
async def simulate_call(req: SimulationRequest):
    """
    Endpoint per simulare una telefonata e l'estrazione dati.
    """
    # 1. Analizza la trascrizione con Gemini
    ai_data = parse_transcript_with_gemini(req.transcript)
    
    # 2. Formatta il report WhatsApp
    report_text = format_whatsapp_report(ai_data, req.customer_phone, req.recording_url)
    
    # 3. Salva nello storico
    import uuid
    call_record = {
        "id": f"sim-{str(uuid.uuid4())[:8]}",
        "phone": req.customer_phone,
        "transcript": req.transcript,
        "recording_url": req.recording_url,
        "ai_data": ai_data,
        "report_text": report_text,
        "type": "simulata"
    }
    save_call(call_record)
    
    # 4. Invia a WhatsApp reale (se configurato)
    whatsapp_status = await send_to_whatsapp(report_text, req.recording_url)
    
    return {
        "call_record": call_record,
        "whatsapp_sent": whatsapp_status
    }

@app.get("/api/calls")
async def get_calls():
    """
    Restituisce lo storico delle chiamate registrate.
    """
    return JSONResponse(content=load_calls())

# --- INTERFACCIA WEB LOCALE (DASHBOARD) ---

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """
    Ritorna una bellissima dashboard web responsive per simulare ed esaminare i risultati telefonici.
    """
    # Leggiamo il system prompt per mostrarlo sulla dashboard
    system_prompt = ""
    try:
        with open("system_prompt.txt", "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except:
        system_prompt = "Prompt non trovato."

    html_content = f"""
<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Truck AI Phone Responder - Dashboard</title>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;500;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --primary: #1E3A8A; /* Blu Scuro Professionale */
      --primary-light: #3B82F6;
      --accent: #F59E0B; /* Giallo Truck */
      --bg: #0F172A; /* Slate scuro premium */
      --card-bg: #1E293B;
      --text: #F8FAFC;
      --text-muted: #94A3B8;
      --border: #334155;
      --success: #10B981;
      --danger: #EF4444;
      --radius: 16px;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      font-family: 'Inter', sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.6;
      padding-bottom: 50px;
    }}
    header {{
      background: linear-gradient(135deg, #1E3B8B 0%, #0F172A 100%);
      padding: 24px 40px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--border);
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }}
    header h1 {{
      font-family: 'Outfit', sans-serif;
      font-size: 26px;
      font-weight: 800;
      letter-spacing: -0.5px;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    header h1 span {{
      color: var(--accent);
    }}
    .badge-live {{
      background-color: rgba(16, 185, 129, 0.2);
      color: var(--success);
      border: 1px solid var(--success);
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.5px;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .badge-live::before {{
      content: '';
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background-color: var(--success);
      animation: pulse 1.5s infinite;
    }}
    @keyframes pulse {{
      0% {{ transform: scale(0.9); opacity: 0.6; }}
      50% {{ transform: scale(1.2); opacity: 1; }}
      100% {{ transform: scale(0.9); opacity: 0.6; }}
    }}
    .container {{
      max-width: 1280px;
      margin: 30px auto;
      padding: 0 20px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 30px;
    }}
    @media (max-width: 900px) {{
      .container {{
        grid-template-columns: 1fr;
      }}
    }}
    .card {{
      background-color: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 24px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.15);
      position: relative;
      overflow: hidden;
    }}
    .card h2 {{
      font-family: 'Outfit', sans-serif;
      font-size: 20px;
      font-weight: 600;
      margin-bottom: 20px;
      border-bottom: 2px solid var(--border);
      padding-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .form-group {{
      margin-bottom: 16px;
    }}
    .form-group label {{
      display: block;
      font-size: 12px;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 6px;
    }}
    .form-group input, .form-group textarea {{
      width: 100%;
      background-color: #0F172A;
      border: 1.5px solid var(--border);
      border-radius: 10px;
      color: var(--text);
      padding: 12px;
      font-size: 14px;
      outline: none;
      transition: border-color 0.2s;
    }}
    .form-group textarea {{
      height: 160px;
      resize: vertical;
      font-family: 'Inter', sans-serif;
    }}
    .form-group input:focus, .form-group textarea:focus {{
      border-color: var(--primary-light);
    }}
    .btn {{
      background: linear-gradient(135deg, var(--primary-light) 0%, var(--primary) 100%);
      color: #fff;
      border: none;
      border-radius: 10px;
      padding: 12px 24px;
      font-size: 15px;
      font-weight: 700;
      cursor: pointer;
      width: 100%;
      box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
      transition: transform 0.1s, opacity 0.2s;
    }}
    .btn:active {{
      transform: scale(0.98);
    }}
    .btn:disabled {{
      opacity: 0.5;
      cursor: not-allowed;
    }}
    .preset-btns {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 20px;
    }}
    .preset-btn {{
      background-color: #334155;
      color: var(--text);
      border: none;
      border-radius: 20px;
      padding: 6px 14px;
      font-size: 12px;
      cursor: pointer;
      font-weight: 500;
      transition: background-color 0.2s;
    }}
    .preset-btn:hover {{
      background-color: var(--primary-light);
    }}
    /* STILING HISTORIC CALLS */
    .calls-list {{
      display: flex;
      flex-direction: column;
      gap: 16px;
      max-height: 700px;
      overflow-y: auto;
      padding-right: 4px;
    }}
    .call-item {{
      background-color: #0F172A;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
      transition: transform 0.2s, border-color 0.2s;
    }}
    .call-item:hover {{
      border-color: var(--primary-light);
    }}
    .call-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }}
    .call-phone {{
      font-weight: 700;
      font-size: 15px;
      color: var(--primary-light);
    }}
    .call-badge {{
      font-size: 11px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 8px;
      text-transform: uppercase;
    }}
    .call-badge.simulata {{
      background-color: rgba(245, 158, 11, 0.15);
      color: var(--accent);
      border: 1px solid var(--accent);
    }}
    .call-badge.reale {{
      background-color: rgba(16, 185, 129, 0.15);
      color: var(--success);
      border: 1px solid var(--success);
    }}
    .grid-data {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-bottom: 12px;
    }}
    .data-box {{
      background-color: rgba(30, 41, 59, 0.5);
      padding: 8px 12px;
      border-radius: 8px;
      font-size: 13px;
    }}
    .data-box strong {{
      display: block;
      color: var(--text-muted);
      font-size: 10px;
      text-transform: uppercase;
      margin-bottom: 2px;
    }}
    .urgency-badge {{
      display: inline-block;
      font-weight: 700;
      font-size: 12px;
      padding: 1px 6px;
      border-radius: 4px;
    }}
    .urgency-badge.alta {{
      background-color: var(--danger);
      color: #fff;
    }}
    .urgency-badge.normale {{
      background-color: var(--primary);
      color: #fff;
    }}
    .whatsapp-preview {{
      background-color: #075E54;
      color: #fff;
      font-family: 'Inter', sans-serif;
      padding: 12px 16px;
      border-radius: 12px;
      font-size: 13px;
      white-space: pre-wrap;
      margin-top: 10px;
      border-left: 4px solid #128C7E;
    }}
    .audio-player {{
      margin-top: 10px;
      width: 100%;
      height: 36px;
    }}
    /* ACCORDION PER IL PROMPT */
    .prompt-box {{
      background-color: #0F172A;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px;
      font-size: 12px;
      color: var(--text-muted);
      white-space: pre-wrap;
      max-height: 180px;
      overflow-y: auto;
      margin-top: 14px;
      font-family: monospace;
    }}
  </style>
</head>
<body>
  <header>
    <h1>🚚 Truck AI <span>Phone Responder</span></h1>
    <div style="display:flex;gap:14px;align-items:center">
      <div class="badge-live">LIVE MONITORING</div>
    </div>
  </header>

  <div class="container">
    <!-- SINISTRA: SIMULATORE -->
    <div style="display:flex;flex-direction:column;gap:30px">
      <div class="card">
        <h2>📞 Simulatore Chiamata Truck</h2>
        <div class="preset-btns">
          <button class="preset-btn" onclick="loadPreset(1)">🔧 Caso 1: Targa scandita + Alternatore (Urgenza)</button>
          <button class="preset-btn" onclick="loadPreset(2)">🚛 Caso 2: Preventivo Standard Pastiglie</button>
          <button class="preset-btn" onclick="loadPreset(3)">⚠️ Caso 3: Telaio + Soffione Sospensione</button>
        </div>

        <div class="form-group">
          <label>Numero Telefonico Cliente</label>
          <input type="text" id="phone" value="+39 345 8899123">
        </div>

        <div class="form-group">
          <label>Trascrizione Vocale Telefonata (Simulata)</label>
          <textarea id="transcript" placeholder="Pasticcia o incolla qui la trascrizione vocale della telefonata..."></textarea>
        </div>

        <button class="btn" id="btn-process" onclick="processSimulation()">✨ Invia & Elabora con Gemini AI</button>
      </div>

      <div class="card">
        <h2>🤖 Prompt di Istruzioni Sistema AI</h2>
        <div style="font-size:13px;color:var(--text-muted)">
          Questo prompt guida le domande dell'agente ed insiste affinché la targa venga dettata città per città.
        </div>
        <div class="prompt-box">{system_prompt}</div>
      </div>
    </div>

    <!-- DESTRA: STORICO E REAL-TIME NOTIFICATIONS -->
    <div class="card">
      <h2>🚨 Notifiche WhatsApp & Storico Richieste</h2>
      <div id="no-calls" style="text-align:center;padding:40px;color:var(--text-muted);display:none">
        Nessuna richiesta ricevuta. Esegui una simulazione a sinistra!
      </div>
      <div class="calls-list" id="calls-list">
        <!-- Chiamate popolate dinamicamente -->
      </div>
    </div>
  </div>

  <script>
    const PRESETS = {{
      1: "Assistente: Benvenuto in Ricambi Truck Ferrara! Io sono l'assistente virtuale. Posso raccogliere la tua richiesta così ti richiamiamo subito. Mi dici il tuo nome e per quale azienda chiami?\\nCliente: Ciao, sono Giovanni dell'Officina Meccanica Emiliana.\\nAssistente: Grazie Giovanni. Mi serve la targa o il telaio del camion per favore. Dettamela scandendo le lettere con i nomi delle città.\\nCliente: Ciao, sì, allora, la targa è Bologna, Torino, zero nove sei, Domodossola, Firenze. Quindi Bologna, Torino, zero nove sei, Domodossola, Firenze.\\nAssistente: Perfetto, registrata. Che ricambio ti serve esattamente per questo mezzo?\\nCliente: Senti, ho un Iveco Stralis con l'alternatore che ci ha abbandonati, si è bruciato del tutto. Potete verificare se lo avete disponibile da ventiquattro volt?\\nAssistente: Capito. Il camion è fermo in panne per questa cosa o si tratta di una manutenzione ordinaria?\\nCliente: Eh sì, il camion è fermo in autostrada in cantiere, ho il cliente bloccato con il carico, ho bisogno che mi facciate sapere al più presto se ce l'avete a magazzino.\\nAssistente: Molto bene, ho registrato tutto con urgenza. Sto inviando subito la trascrizione al team dei ricambisti. Ti richiamiamo tra pochissimi minuti! Grazie e a presto!",
      
      2: "Assistente: Benvenuto in Ricambi Truck Ferrara! Io sono l'assistente virtuale. Posso raccogliere la tua richiesta così ti richiamiamo subito. Mi dici il tuo nome e per quale azienda chiami?\\nCliente: Ciao, sono Antonio della ditta Autotrasporti Ferrara SRL.\\nAssistente: Grazie Antonio. Mi serve la targa o il telaio del camion per favore. Dettamela scandendo le lettere con i nomi delle città.\\nCliente: Allora, la targa è Ancona, Como, sette due quattro, Venezia, Genova.\\nAssistente: Perfetto, registrata. Che ricambio ti serve esattamente per questo mezzo?\\nCliente: Dobbiamo fare un intervento programmato per sabato. Mi servirebbe un kit completo di pastiglie e dischi freno anteriori per un MAN TGX del duemilaventi. Volevo un preventivo di spesa.\\nAssistente: Capito. Il camion è fermo in panne per questa cosa o si tratta di una manutenzione ordinaria?\\nCliente: No no, manutenzione ordinaria in officina da noi sabato mattina, quindi con calma, mandatemi pure un WhatsApp appena avete il prezzo.\\nAssistente: Molto bene! Ho raccolto tutte le informazioni. Invio la notifica al reparto ricambi. Ti richiamiamo o ti scriviamo a breve. Grazie!",
      
      3: "Assistente: Benvenuto in Ricambi Truck Ferrara! Io sono l'assistente virtuale. Posso raccogliere la tua richiesta così ti richiamiamo subito. Mi dici il tuo nome e per quale azienda chiami?\\nCliente: Ciao sono Roberto. Chiamo per conto mio, sono un padroncino.\\nAssistente: Grazie Roberto. Mi serve la targa o il telaio del camion per favore. Dettamela scandendo le lettere con i nomi delle città.\\nCliente: Guarda non ricordo la targa a mente ma ho qui la carta di circolazione con il telaio. Il finale del telaio è ZLA quattro cinque sei sette otto nove zero.\\nAssistente: Perfetto, registrato il telaio. Che ricambio ti serve esattamente per questo mezzo?\\nCliente: Mi serve urgentemente il soffione della sospensione pneumatica posteriore destra. Mi si è spaccato stamattina mentre caricavo.\\nAssistente: Capito. Il camion è fermo in panne per questa cosa o si tratta di una manutenzione ordinaria?\\nCliente: Eh sì, il camion è accasciato da un lato ed è fermo in officina da me, non posso viaggiare. È abbastanza urgente.\\nAssistente: Molto bene, ho registrato tutto con urgenza. Sto inviando subito la trascrizione al team dei ricambisti. Ti richiamiamo tra pochissimi minuti! Grazie e a presto!"
    }};

    function loadPreset(id) {{
      document.getElementById('transcript').value = PRESETS[id].replace(/\\n/g, '\\n');
    }}

    // Carica il preset 1 all'avvio
    window.onload = function() {{
      loadPreset(1);
      fetchCalls();
    }};

    async function fetchCalls() {{
      try {{
        const response = await fetch('/api/calls');
        const data = await response.json();
        const list = document.getElementById('calls-list');
        const noCalls = document.getElementById('no-calls');
        
        list.innerHTML = '';
        if (data.length === 0) {{
          noCalls.style.display = 'block';
          return;
        }}
        noCalls.style.display = 'none';

        data.forEach(call => {{
          const isAlta = call.ai_data.urgenza.includes('ALTA');
          const item = document.createElement('div');
          item.className = 'call-item';
          item.innerHTML = `
            <div class="call-header">
              <span class="call-phone">📞 ${{call.phone}}</span>
              <span class="call-badge ${{call.type}}">${{call.type}}</span>
            </div>
            <div class="grid-data">
              <div class="data-box">
                <strong>👤 Cliente</strong>
                ${{call.ai_data.cliente}}
              </div>
              <div class="data-box">
                <strong>🚚 Targa/Telaio Ricostruito</strong>
                <code style="font-weight:700;color:var(--accent)">${{call.ai_data.targa_telaio_ricostruita}}</code>
              </div>
              <div class="data-box">
                <strong>⚠️ Urgenza</strong>
                <span class="urgency-badge ${{isAlta ? 'alta' : 'normale'}}">${{call.ai_data.urgenza}}</span>
              </div>
              <div class="data-box">
                <strong>📢 Sintesi</strong>
                ${{call.ai_data.sintesi}}
              </div>
            </div>
            
            <div class="form-group" style="margin-top:10px">
              <label>🛠️ Pezzi Rilevati</label>
              <div style="font-size:13px;color:#cbd5e1;padding-left:10px">
                ${{call.ai_data.ricambi_richiesti.map(r => '• ' + r).join('<br> ')}}
              </div>
            </div>

            <div class="form-group" style="margin-top:10px">
              <label>📝 Anteprima Notifica WhatsApp Aziendale</label>
              <div class="whatsapp-preview">${{call.report_text}}</div>
            </div>

            <audio class="audio-player" controls>
              <source src="${{call.recording_url}}" type="audio/mpeg">
              Il browser non supporta l'ascolto audio.
            </audio>
          `;
          list.appendChild(item);
        }});
      }} catch (e) {{
        console.error("Errore nel caricamento dello storico:", e);
      }}
    }}

    async function processSimulation() {{
      const btn = document.getElementById('btn-process');
      const transcript = document.getElementById('transcript').value.trim();
      const phone = document.getElementById('phone').value.trim();

      if (!transcript) {{
        alert("Inserisci o carica una trascrizione prima di procedere.");
        return;
      }}

      btn.disabled = true;
      btn.textContent = "Elaborazione in corso con Gemini AI...";

      try {{
        const response = await fetch('/api/simulate', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ transcript, customer_phone: phone }})
        }});

        if (response.ok) {{
          alert("Chiamata elaborata con successo! Notifica simulata aggiunta allo storico.");
          await fetchCalls();
        }} else {{
          alert("Si è verificato un errore durante l'elaborazione.");
        }}
      }} catch (e) {{
        console.error("Errore nella simulazione:", e);
        alert("Errore di rete durante la connessione al server.");
      }} finally {{
        btn.disabled = false;
        btn.textContent = "✨ Invia & Elabora con Gemini AI";
      }}
    }}
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)
