import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
from openai import OpenAI

from fastapi.middleware.cors import CORSMiddleware

# Importazione configurazioni locali
try:
    from config import ROOMS_DB, HOTEL_NAME, DIRECT_BOOKING_BENEFIT, OPENAI_API_KEY, GEMINI_API_KEY
except ImportError:
    # Fallback in caso di avvio isolato
    ROOMS_DB = []
    HOTEL_NAME = "Boutique Hotel S'Antiga"
    DIRECT_BOOKING_BENEFIT = "welcome drink + SPA access"
    OPENAI_API_KEY = "your_key"
    GEMINI_API_KEY = "your_key"

import os
# Rilevamento della chiave API da utilizzare
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY or API_KEY == "your_gemini_api_key_here":
    API_KEY = os.getenv("OPENAI_API_KEY")
    if not API_KEY or API_KEY == "your_openai_api_key_here":
        # Se non trovate in ambiente, proviamo le variabili importate da config.py
        if 'GEMINI_API_KEY' in globals() and GEMINI_API_KEY and GEMINI_API_KEY != "your_key" and GEMINI_API_KEY != "your_gemini_api_key_here":
            API_KEY = GEMINI_API_KEY
        else:
            API_KEY = OPENAI_API_KEY

# Configurazione Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AI-Concierge-BoutiqueHotel")

app = FastAPI(
    title="AI Concierge - Boutique Hotel S'Antiga",
    description="Prototipo di backend per l'integrazione di OpenAI Function Calling con il PMS Slope/Octorate",
    version="1.0.0"
)

# Abilitazione CORS per consentire l'interazione con il browser locale
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inizializzazione client (rilevamento automatico se si tratta di una chiave Google Gemini)
IS_GEMINI = API_KEY.startswith("AIzaSy") or "gemini" in API_KEY.lower()

if IS_GEMINI:
    logger.info("[CONFIG] Rilevata chiave Gemini. Configuro il client per Google Generative Language API.")
    client = OpenAI(
        api_key=API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    DEFAULT_MODEL = "gemini-2.5-flash"
else:
    logger.info("[CONFIG] Configuro il client per OpenAI standard.")
    client = OpenAI(api_key=API_KEY)
    DEFAULT_MODEL = "gpt-4o"

# Database in memoria per simulare le prenotazioni/blocchi provvisori
reservations_db: List[Dict[str, Any]] = []

# Dizionario in memoria per la memoria conversazionale (simulazione Redis)
chat_sessions: Dict[str, List[Dict[str, Any]]] = {}

# --- MODELLI PYDANTIC PER LE API ---
class MessageInput(BaseModel):
    user_id: str          # Identificativo unico utente (es. numero WhatsApp)
    message: str          # Messaggio inviato dall'utente
    user_name: Optional[str] = "Ospite"

class BookingHoldInput(BaseModel):
    guest_name: str
    guest_email: str
    guest_phone: str
    checkin: str
    checkout: str
    room_type_id: str

# --- STRUMENTI MOCK DEL PMS (Slope / Octorate API) ---

def pms_check_availability(checkin: str, checkout: str, guests: int) -> List[Dict[str, Any]]:
    """
    Simula l'interrogazione API del PMS per controllare le camere disponibili.
    """
    logger.info(f"[PMS API] Controllo disponibilità per {checkin} -> {checkout} per {guests} ospiti.")
    
    # Simula una logica di calcolo giorni
    try:
        d1 = datetime.strptime(checkin, "%Y-%m-%d")
        d2 = datetime.strptime(checkout, "%Y-%m-%d")
        nights = (d2 - d1).days
        if nights <= 0:
            return []
    except Exception:
        # Fallback se le date non sono nel formato corretto
        nights = 3

    available_rooms = []
    for room in ROOMS_DB:
        if guests <= room["max_occupancy"] and room["available_units"] > 0:
            total_price = room["price_per_night"] * nights
            available_rooms.append({
                "room_type_id": room["id"],
                "room_name": room["name"],
                "price_per_night": room["price_per_night"],
                "total_price": total_price,
                "nights": nights,
                "benefits_included": DIRECT_BOOKING_BENEFIT
            })
    return available_rooms

def pms_create_temporary_hold(data: BookingHoldInput) -> Dict[str, Any]:
    """
    Simula la creazione di un blocco camera provvisorio (opzione di 24 ore) nel PMS.
    """
    logger.info(f"[PMS API] Creazione blocco provvisorio per {data.guest_name} - Camera: {data.room_type_id}")
    
    hold_id = f"HLD-{int(datetime.now().timestamp())}"
    new_hold = {
        "hold_id": hold_id,
        "guest_name": data.guest_name,
        "guest_email": data.guest_email,
        "guest_phone": data.guest_phone,
        "checkin": data.checkin,
        "checkout": data.checkout,
        "room_type_id": data.room_type_id,
        "status": "TEMPORARY_HOLD",
        "expiration": "Valido per 24 ore. Per confermare, completa il pagamento tramite il link sicuro inviato via email."
    }
    reservations_db.append(new_hold)
    return new_hold

# --- ENGINE AI & ORCHESTRAZIONE FUNCTION CALLING ---

# Definizione dei Tools per OpenAI
TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "check_room_availability",
            "description": "Verifica le camere disponibili del boutique hotel in base alle date di check-in, check-out e al numero di ospiti.",
            "parameters": {
                "type": "object",
                "properties": {
                    "checkin": {
                        "type": "string",
                        "description": "Data di check-in in formato YYYY-MM-DD (es. 2026-06-15)"
                    },
                    "checkout": {
                        "type": "string",
                        "description": "Data di check-out in formato YYYY-MM-DD (es. 2026-06-22)"
                    },
                    "guests": {
                        "type": "integer",
                        "description": "Numero totale di ospiti per camera"
                    }
                },
                "required": ["checkin", "checkout", "guests"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_temporary_hold",
            "description": "Blocca provvisoriamente una camera specifica per un ospite inserendo i suoi dati per 24 ore nel PMS.",
            "parameters": {
                "type": "object",
                "properties": {
                    "guest_name": {
                        "type": "string",
                        "description": "Nome e Cognome del cliente"
                    },
                    "guest_email": {
                        "type": "string",
                        "description": "Indirizzo e-mail del cliente"
                    },
                    "guest_phone": {
                        "type": "string",
                        "description": "Numero di telefono cellulare"
                    },
                    "checkin": {
                        "type": "string",
                        "description": "Data di inizio soggiorno YYYY-MM-DD"
                    },
                    "checkout": {
                        "type": "string",
                        "description": "Data di fine soggiorno YYYY-MM-DD"
                    },
                    "room_type_id": {
                        "type": "string",
                        "description": "ID identificativo della stanza scelto (es. deluxe_mare, junior_suite, classic_giardino)"
                    }
                },
                "required": ["guest_name", "guest_email", "guest_phone", "checkin", "checkout", "room_type_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_human_handover",
            "description": "Richiede l'intervento immediato di un operatore umano dello staff della reception dell'hotel per gestire richieste complesse, lamentele o preventivi personalizzati di gruppo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Motivo dettagliato del passaggio ad operatore umano"
                    }
                },
                "required": ["reason"]
            }
        }
    }
]

SYSTEM_PROMPT = f"""Sei "Sanna", l'AI Brand Concierge virtuale del lussuoso {HOTEL_NAME}, situato in Sardegna.
Il tuo obiettivo è accogliere i clienti con calore, estrema cortesia ed eleganza, rispecchiando i valori dell'ospitalità sarda.

LINEE GUIDA COMPORTAMENTALI:
1. Tono: Elegante, caloroso, accogliente e servizievole. Non usare risposte robotiche. Fai sentire l'utente a casa.
2. Lingua: Rispondi sempre nella stessa lingua usata dall'utente (Italiano, Inglese, Tedesco, Francese, ecc.).
3. Promozione Prenotazioni Dirette: Quando offri preventivi o disponibilità di stanze, menziona SEMPRE con orgoglio che prenotando direttamente con te avranno diritto a un eccezionale vantaggio esclusivo: {DIRECT_BOOKING_BENEFIT}.
4. Consigli Proattivi: Se consigliano spiagge o uscite in barca, proponi di prenotare con lo staff il pranzo al sacco dell'hotel.
5. In caso di dubbi sulla disponibilità, usa lo strumento `check_room_availability`.
6. Se l'utente decide di bloccare una camera, chiedi i dati necessari ed esegui lo strumento `create_temporary_hold`.
7. Se l'utente esprime irritazione, richiede espressamente un operatore umano o desidera preventivi speciali fuori catalogo (es. matrimoni, meeting aziendali), invoca lo strumento `trigger_human_handover`.
"""

def execute_tool_call(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Esegue fisicamente la funzione locale associata alla chiamata dell'LLM.
    """
    if name == "check_room_availability":
        results = pms_check_availability(
            checkin=arguments["checkin"],
            checkout=arguments["checkout"],
            guests=arguments.get("guests", 2)
        )
        return {"status": "success", "available_rooms": results}
        
    elif name == "create_temporary_hold":
        hold_data = BookingHoldInput(
            guest_name=arguments["guest_name"],
            guest_email=arguments["guest_email"],
            guest_phone=arguments["guest_phone"],
            checkin=arguments["checkin"],
            checkout=arguments["checkout"],
            room_type_id=arguments["room_type_id"]
        )
        result = pms_create_temporary_hold(hold_data)
        return {"status": "success", "hold_details": result}
        
    elif name == "trigger_human_handover":
        logger.warning(f"[HANDOVER RETRIEVAL] Richiesto passaggio ad operatore umano. Motivo: {arguments['reason']}")
        return {
            "status": "handover_active",
            "message": "Staff allertato. Un operatore umano della reception prenderà il controllo della conversazione entro pochi minuti."
        }
        
    else:
        return {"status": "error", "message": f"Strumento {name} non supportato."}

# --- ENDPOINTS API ---

@app.get("/")
def read_root():
    """
    Serve la splendida dashboard web per il test interattivo del prototipo.
    """
    try:
        with open("index.html", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except Exception as e:
        logger.error(f"Errore caricamento index.html: {e}")
        return HTMLResponse(content=f"<h1>AI Concierge {HOTEL_NAME} online</h1><p>Inserisci il file index.html nella cartella di lavoro.</p>", status_code=200)

@app.get("/api/pms/rooms")
def get_pms_rooms():
    return ROOMS_DB

@app.get("/api/pms/holds")
def get_pms_holds():
    return reservations_db

@app.post("/api/pms/reset")
def reset_pms_demo():
    global reservations_db, chat_sessions
    reservations_db.clear()
    chat_sessions.clear()
    return {"status": "success", "message": "Sessioni e prenotazioni resettate con successo!"}

@app.post("/webhook/whatsapp")
def whatsapp_webhook(input_data: MessageInput):
    """
    Punto di ingresso che simula la ricezione di un messaggio da WhatsApp (Webhook Meta).
    Gestisce la conversazione, chiama OpenAI, valuta i tool e restituisce la risposta.
    """
    user_id = input_data.user_id
    user_msg = input_data.message
    
    # Inizializza la cronologia della sessione se non esiste
    if user_id not in chat_sessions:
        chat_sessions[user_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        
    session_history = chat_sessions[user_id]
    
    # Aggiungi il nuovo messaggio dell'utente alla cronologia
    session_history.append({"role": "user", "content": user_msg})
    
    try:
        # Se la chiave API non è configurata o è di default, restituiamo un mock elegante per consentire il test locale immediato senza fallimenti
        # Se la chiave API non è configurata o è di default, restituiamo un mock elegante per consentire il test locale immediato senza fallimenti
        is_valid_key = API_KEY.startswith("sk-") or API_KEY.startswith("AIzaSy") or IS_GEMINI
        if API_KEY in ["your_openai_api_key_here", "your_gemini_api_key_here", "your_key", ""] or not is_valid_key:
            logger.warning("[WARNING] API Key non configurata o non valida. Restituisco mock di cortesia.")
            return process_mock_response(user_msg, input_data.user_name)

        # Chiamata a OpenAI/Gemini con supporto per i Tools
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=session_history,
            tools=TOOLS_DEFINITION,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        # Gestione del Tool Calling (se l'AI ha deciso di usare uno strumento)
        if response_message.tool_calls:
            # Aggiungiamo il messaggio dell'assistente che richiede il tool alla cronologia
            session_history.append(response_message)
            
            # Eseguiamo ciascuna chiamata di strumento richiesta
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Eseguiamo l'azione locale
                tool_output = execute_tool_call(function_name, function_args)
                
                # Aggiungiamo il risultato dello strumento alla cronologia
                session_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(tool_output)
                })
            
            # Richiediamo una seconda risposta fornendo i dati dello strumento
            second_response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=session_history
            )
            
            assistant_reply = second_response.choices[0].message.content
            session_history.append({"role": "assistant", "content": assistant_reply})
            
            # Determiniamo se lo strumento eseguito era l'handover umano
            is_handover = any(tc.function.name == "trigger_human_handover" for tc in response_message.tool_calls)
            
            # Estraiamo i tool chiamati per mostrarli sulla dashboard
            tool_calls_data = []
            for tc in response_message.tool_calls:
                tool_calls_data.append({
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments)
                })
            
            return {
                "sender": "Sanna (AI Concierge)",
                "reply": assistant_reply,
                "session_active": not is_handover,
                "handover_triggered": is_handover,
                "tool_calls": tool_calls_data
            }
            
        else:
            # Risposta semplice dell'assistente (senza uso di strumenti)
            assistant_reply = response_message.content
            session_history.append({"role": "assistant", "content": assistant_reply})
            
            return {
                "sender": "Sanna (AI Concierge)",
                "reply": assistant_reply,
                "session_active": True,
                "handover_triggered": False,
                "tool_calls": []
            }
            
    except Exception as e:
        logger.error(f"[ERROR] Errore nell'elaborazione del messaggio: {e}")
        # Ritorna comunque una risposta simulata robusta in caso di errore di connessione/chiave
        return process_mock_response(user_msg, input_data.user_name)

def process_mock_response(user_msg: str, user_name: str) -> Dict[str, Any]:
    """
    Fornisce risposte simulate intelligenti per testare localmente il flusso
    anche in assenza di chiavi OpenAI configurate.
    """
    msg = user_msg.lower()
    reply = ""
    handover = False
    
    if "blocca" in msg or "prenot" in msg:
        reply = (
            f"Certamente {user_name}! Ho appena effettuato un blocco provvisorio (Opzione Opzionata) nel nostro gestionale PMS "
            f"per la camera **Deluxe Vista Mare** a tuo nome! Codice opzione: **HLD-99812**. 📝\n\n"
            f"Ti ho inviato un'email con il riepilogo e il link sicuro per completare la conferma. La tua camera è al sicuro "
            f"per le prossime 24 ore! Non vedo l'ora di farti degustare il nostro Vermentino di Gallura al tuo arrivo!"
        )
    elif "disponib" in msg or "camer" in msg or "stanz" in msg or "cost" in msg or "prezz" in msg:
        reply = (
            f"Benvenuto a bordo {user_name}! Ho interrogato all'istante il nostro PMS ed ecco le disponibilità "
            f"per te per le prossime settimane. Ti ricordo con orgoglio che prenotando direttamente tramite questa chat "
            f"otterrai subito l'esclusivo **{DIRECT_BOOKING_BENEFIT}**! 🍷✨\n\n"
            f"1. **Classic Vista Giardino**: 180€ a notte (5 unità libere)\n"
            f"2. **Deluxe Vista Mare**: 250€ a notte (3 unità libere) — *Fortemente raccomandata!*\n"
            f"3. **Junior Suite con Jacuzzi**: 420€ a notte (Solo 1 rimasta!)\n\n"
            f"Desideri che blocchi una di queste opzioni a tuo nome gratuitamente per 24 ore?"
        )
    elif "umano" in msg or "staff" in msg or "parlare con" in msg or "reception" in msg or "lament" in msg:
        reply = (
            f"Capisco perfettamente {user_name}. Sto passando immediatamente la nostra conversazione a un collega umano "
            f"dello staff della reception. Sarà con te tra pochissimi istanti su questo canale per darti massima assistenza. "
            f"A presto!"
        )
        handover = True
    else:
        reply = (
            f"Felice di conoscerti, {user_name}! Sono Sanna, il concierge digitale del Boutique Hotel S'Antiga. "
            f"Posso aiutarti a trovare la camera perfetta (offrendoti i fantastici vantaggi della prenotazione diretta!), "
            f"raccontarti i dettagli dei nostri servizi SPA e ristorante, o darti consigli sulle spiagge più belle del sud Sardegna. "
            f"Come posso coccolarti oggi?"
        )
        
    simulated_tools = []
    if "blocca" in msg or "prenot" in msg:
        simulated_tools.append({
            "name": "create_temporary_hold",
            "arguments": {
                "guest_name": user_name,
                "guest_email": "marco@email.it",
                "guest_phone": "+393401122334",
                "checkin": "2026-06-15",
                "checkout": "2026-06-22",
                "room_type_id": "deluxe_mare"
            }
        })
    elif "disponib" in msg or "camer" in msg or "stanz" in msg or "cost" in msg or "prezz" in msg:
        simulated_tools.append({
            "name": "check_room_availability",
            "arguments": {
                "checkin": "2026-06-15",
                "checkout": "2026-06-22",
                "guests": 2
            }
        })
    elif "umano" in msg or "staff" in msg or "parlare con" in msg or "reception" in msg or "lament" in msg:
        simulated_tools.append({
            "name": "trigger_human_handover",
            "arguments": {
                "reason": "Richiesta preventivo speciale compleanno"
            }
        })

    return {
        "sender": "Sanna (AI Concierge - Mock Engine)",
        "reply": reply,
        "session_active": not handover,
        "handover_triggered": handover,
        "tool_calls": simulated_tools
    }

# --- RUNNER ---
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
