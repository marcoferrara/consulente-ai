import os
import json
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import google.generativeai as genai
import dotenv

# Load environment variables
dotenv.load_dotenv(dotenv_path="../.env")
dotenv.load_dotenv()  # also check local folder

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("voice_calling_bot")

app = FastAPI(title="La Sorgente — Outbound Voice Bot Simulation")

# Database Path
DB_PATH = os.path.join(os.path.dirname(__file__), "database.json")

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
gemini_active = False

if api_key:
    try:
        genai.configure(api_key=api_key)
        # Test model availability
        model = genai.GenerativeModel("gemini-2.5-flash")
        gemini_active = True
        logger.info("Gemini API configurata con successo per il Voice Bot.")
    except Exception as e:
        logger.error(f"Errore nella configurazione di Gemini API: {e}")
else:
    logger.warning("GEMINI_API_KEY non trovata. Verrà utilizzata la simulazione locale dei dialoghi.")

def read_db():
    if not os.path.exists(DB_PATH):
        # Fallback if file missing
        return {"leads": [], "settings": {"system_prompt": "Sei l'assistente vocale dell'Accademia."}}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def write_db(data):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Serve templates and assets
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(TEMPLATES_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Frontend non trovato. Esegui il build.")

# API ENDPOINTS
@app.get("/api/leads")
async def get_leads():
    db = read_db()
    return db.get("leads", [])

@app.post("/api/leads")
async def add_lead(lead: dict = Body(...)):
    db = read_db()
    new_id = f"lead_{len(db['leads']) + 1:03d}"
    lead["id"] = new_id
    lead["status"] = "Da Chiamare"
    lead["call_date"] = None
    lead["duration"] = 0
    lead["transcript"] = []
    lead["sentiment"] = None
    lead["outcome"] = None
    db["leads"].append(lead)
    write_db(db)
    return {"status": "success", "lead": lead}

@app.delete("/api/leads/{lead_id}")
async def delete_lead(lead_id: str):
    db = read_db()
    db["leads"] = [l for l in db["leads"] if l["id"] != lead_id]
    write_db(db)
    return {"status": "success", "message": "Lead eliminato"}

@app.post("/api/leads/reset")
async def reset_leads():
    db = read_db()
    for l in db["leads"]:
        l["status"] = "Da Chiamare"
        l["call_date"] = None
        l["duration"] = 0
        l["transcript"] = []
        l["sentiment"] = None
        l["outcome"] = None
    write_db(db)
    return {"status": "success", "message": "Stato dei lead resettato con successo"}

@app.get("/api/settings")
async def get_settings():
    db = read_db()
    return db.get("settings", {"system_prompt": ""})

@app.post("/api/settings")
async def save_settings(settings: dict = Body(...)):
    db = read_db()
    db["settings"] = settings
    write_db(db)
    return {"status": "success", "message": "Impostazioni salvate con successo"}

@app.post("/api/calls/trigger/{lead_id}")
async def trigger_call(lead_id: str):
    db = read_db()
    lead = next((l for l in db["leads"] if l["id"] == lead_id), None)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead non trovato")
    
    lead["status"] = "In Chiamata"
    lead["transcript"] = []
    lead["call_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    write_db(db)
    
    # Generate initial greetings
    system_prompt = db.get("settings", {}).get("system_prompt", "")
    lead_name = f"{lead['first_name']} {lead['last_name']}"
    
    initial_text = f"Salve! Sono l'assistente virtuale dell'Accademia Internazionale del Musical della sede di Cagliari! Parlo con {lead_name}?"
    
    # Log initial AI message
    lead["transcript"].append({"speaker": "AI", "text": initial_text})
    write_db(db)
    
    return {"status": "success", "lead": lead, "initial_text": initial_text}

@app.post("/api/calls/respond/{lead_id}")
async def respond_call(lead_id: str, payload: dict = Body(...)):
    db = read_db()
    lead = next((l for l in db["leads"] if l["id"] == lead_id), None)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead non trovato")
    
    user_text = payload.get("text", "").strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Testo mancante")
    
    # Append lead message
    lead["transcript"].append({"speaker": "Lead", "text": user_text})
    
    system_prompt = db.get("settings", {}).get("system_prompt", "")
      # Inject lead information into system instructions
    context_prompt = f"{system_prompt}\n\nINFORMAZIONI SUL LEAD CORRENTE:\n" \
                     f"- Nome: {lead['first_name']} {lead['last_name']}\n" \
                     f"- Luogo: {lead['city']}\n" \
                     f"- Interesse: {lead['interest']}\n" \
                     f"- Livello: {lead['level']}\n" \
                     f"- Note/Contesto: {lead['notes']}\n\n" \
                     f"Mantieni le risposte brevi ed empatiche. Parla in prima persona come assistente dell'Accademia.\n" \
                     f"IMPORTANTE: Se nella conversazione l'audizione è già stata concordata/fissata (es. il lead ha accettato un orario o un giorno), NON proporre nuovamente l'audizione e non chiedere se desidera partecipare. Ringrazialo semplicemente, auguragli buona giornata o rispondi alle sue eventuali domande specifiche sui costi o dettagli logistici."
                     
    # Generate response
    ai_response = ""
    if gemini_active:
        try:
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=context_prompt
            )
            # Reconstruct chat history for Gemini
            chat = model.start_chat(history=[])
            # Compile conversation history to give full context
            history_text = "Ecco la conversazione avvenuta finora telefonica:\n"
            for t in lead["transcript"][:-1]: # exclude the latest user message
                history_text += f"{t['speaker']}: {t['text']}\n"
            
            # Send latest message with history context
            response = chat.send_message(f"{history_text}\nLead: {user_text}\nGenera ora la risposta dell'AI (breve, max 2 frasi, naturale in italiano):")
            ai_response = response.text.strip()
        except Exception as e:
            logger.error(f"Errore Gemini in respond_call: {e}")
            ai_response = generate_mock_response(user_text, lead)
    else:
        ai_response = generate_mock_response(user_text, lead)
        
    # Append AI message
    lead["transcript"].append({"speaker": "AI", "text": ai_response})
    write_db(db)
    
    return {"status": "success", "text": ai_response}

@app.post("/api/calls/finalize/{lead_id}")
async def finalize_call(lead_id: str, payload: dict = Body(...)):
    db = read_db()
    lead = next((l for l in db["leads"] if l["id"] == lead_id), None)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead non trovato")
    
    duration = payload.get("duration", 0)
    lead["duration"] = duration
    
    # Analyze transcript using Gemini to extract sentiment and outcome
    transcript_str = "\n".join([f"{t['speaker']}: {t['text']}" for l in db["leads"] if l["id"] == lead_id for t in l["transcript"]])
    
    sentiment = "Neutro"
    outcome = "Chiamata Completata"
    
    if gemini_active and len(lead["transcript"]) > 1:
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            analysis_prompt = f"""
            Analizza la seguente trascrizione di una telefonata tra il nostro assistente vocale AI dell'Accademia Internazionale del Musical di Cagliari e un potenziale studente (Lead).
            
            TRASCRIZIONE:
            {transcript_str}
            
            Devi restituire un oggetto JSON contenente esattamente due chiavi:
            1. "sentiment": deve essere obbligatoriamente una tra queste tre stringhe: "Positivo", "Neutro", "Negativo".
            2. "outcome": una descrizione sintetica del risultato (max 6-7 parole, in italiano), ad esempio:
            - "Audizione Fissata (Giorno Ore)" se ha accettato l'audizione.
            - "Da Richiamare (Motivazione)" se ha chiesto di essere richiamato.
            - "Non Interessato (Motivazione)" se ha rifiutato o non è interessato.
            - "Chiamata Interrotta" se si è interrotta prima.
            
            Rispondi esclusivamente con l'oggetto JSON formattato correttamente. Non aggiungere commenti esterni o markdown.
            """
            response = model.generate_content(analysis_prompt)
            clean_res = response.text.replace("```json", "").replace("```", "").strip()
            res_obj = json.loads(clean_res)
            sentiment = res_obj.get("sentiment", "Neutro")
            outcome = res_obj.get("outcome", "Chiamata Completata")
        except Exception as e:
            logger.error(f"Errore analisi Gemini in finalize_call: {e}")
            sentiment, outcome = evaluate_mock_call_outcome(lead["transcript"])
    else:
        sentiment, outcome = evaluate_mock_call_outcome(lead["transcript"])
        
    lead["sentiment"] = sentiment
    lead["outcome"] = outcome
    lead["status"] = "Chiamato"
    
    write_db(db)
    return {"status": "success", "lead": lead}

# MOCK UTILS FOR LOCAL SIMULATION
def generate_mock_response(text: str, lead: dict) -> str:
    text_lower = text.lower()
    lead_name = lead["first_name"]
    course = lead["interest"]
    
    # Check if we already agreed on a date/time in the transcript
    already_scheduled = False
    for t in lead.get("transcript", []):
        t_text = t["text"].lower()
        if "prenotato" in t_text or "riservo lo slot" in t_text or "ti segno per la" in t_text or "ti prenoto" in t_text:
            already_scheduled = True
            break
            
    # Count turns (how many messages in transcript including the current Lead message)
    turns = len(lead.get("transcript", []))
            
    if already_scheduled:
        if "grazie" in text_lower or "ciao" in text_lower or "buona giornata" in text_lower:
            return f"Grazie a te, {lead_name}! È stato un vero piacere. Ti auguro una splendida giornata e a presto!"
        elif "costo" in text_lower or "prezzo" in text_lower or "pagamento" in text_lower:
            return "Riguardo ai prezzi, offriamo borse di studio e rateizzazioni mensili personalizzate. Riceverai tutti i dettagli completi nella mail di conferma dell'audizione!"
        else:
            return f"Perfetto, {lead_name}! Ti confermo che l'audizione è registrata. Ci sentiamo presto e buona giornata!"
            
    # Identity confirmation phase (1st candidate response: turns <= 2)
    if turns <= 2:
        if "sì" in text_lower or "si" in text_lower or "sono io" in text_lower or "confermo" in text_lower:
            return f"Grazie di aver confermato! Ti chiamo proprio in merito alla tua richiesta di informazioni per il {course} qui a Cagliari. Ti andrebbe di fare un'audizione conoscitiva gratuita con i nostri docenti?"

    if "grazie" in text_lower or "ciao" in text_lower or "buongiorno" in text_lower:
        return f"Figurati {lead_name}! È un piacere. Come ti dicevo, siamo l'Accademia del Musical a Cagliari. Saresti interessato a fare un'audizione gratuita con noi?"
    elif "sì" in text_lower or "si" in text_lower or "interessato" in text_lower or "volentieri" in text_lower or "certo" in text_lower or "ok" in text_lower:
        return f"Fantastico! Le prossime audizioni a Cagliari per il {course} si terranno sabato 22 Maggio. Preferisci la mattina o il pomeriggio?"
    elif "no" in text_lower or "non posso" in text_lower or "non mi interessa" in text_lower:
        return "Capisco perfettamente. C'è magari un altro corso d'interesse o preferisci che ti ricontattiamo in un altro momento dell'anno?"
    elif "costo" in text_lower or "prezzo" in text_lower or "pagamento" in text_lower:
        return "I prezzi variano in base alla formula di frequenza e offriamo borse di studio e rateizzazione mensile. Ti spiegheremo tutto nel dettaglio durante l'audizione conoscitiva gratuita!"
    elif "quando" in text_lower or "orario" in text_lower or "dove" in text_lower:
        return "La nostra sede è a Cagliari in Via Dante. Le audizioni si tengono sabato 22 Maggio sia la mattina alle 10:00 sia il pomeriggio alle 15:30. Quale orario ti torna più comodo?"
    elif "pomeriggio" in text_lower or "pomeridiano" in text_lower:
        return "Ottimo, ti riservo lo slot pomeridiano delle 15:30. Ti manderò tutti i dettagli e la mail di conferma per l'Accademia del Musical di Cagliari. Ci sarai?"
    elif "mattina" in text_lower or "mattutino" in text_lower:
        return "Perfetto, ti segno per la mattina alle 10:00. Riceverai a breve una mail con le indicazioni e i brani consigliati. Ci confermi la presenza?"
    else:
        return f"Certo {lead_name}! L'Accademia Internazionale del Musical di Cagliari offre un percorso completo di recitazione, canto e danza con esami AFAM per i crediti universitari. Ti piacerebbe fare un'audizione conoscitiva con i nostri docenti?"

def evaluate_mock_call_outcome(transcript) -> tuple:
    if len(transcript) <= 1:
        return "Neutro", "Chiamata Interrotta"
        
    full_text = " ".join([t["text"].lower() for t in transcript if t["speaker"] == "Lead"])
    
    if "pomeriggio" in full_text or "mattina" in full_text or "va bene" in full_text or "sì" in full_text or "confermo" in full_text:
        return "Positivo", "Audizione Fissata (22 Maggio)"
    elif "no" in full_text or "non mi interessa" in full_text or "rifiuto" in full_text:
        return "Negativo", "Non Interessato (Rifiutato)"
    elif "richiama" in full_text or "richiamami" in full_text or "domani" in full_text or "lavoro" in full_text:
        return "Neutro", "Da Richiamare (Occupato)"
    else:
        return "Neutro", "Chiamata Effettuata"

if __name__ == "__main__":
    import uvicorn
    # Avvia sulla porta 8082 per evitare conflitti con la sorgente hub (8081)
    uvicorn.run("app:app", host="127.0.0.1", port=8082, reload=True)
