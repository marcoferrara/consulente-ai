import json
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from fastapi import FastAPI, Body
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from openai import OpenAI

from fastapi.middleware.cors import CORSMiddleware

# Importazione configurazioni locali
try:
    from config import (
        APARTMENT, MOCK_BOOKED_RANGES, DIRECT_BOOKING_BENEFIT, OWNER_INFO,
        OPENAI_API_KEY, GEMINI_API_KEY
    )
except ImportError:
    # Fallback in caso di avvio isolato
    APARTMENT = {"name": "Gitty&Stella", "slug": "gitty-stella", "max_occupancy": 4,
                 "base_price_per_night": 85.0, "long_stay_discount_threshold_nights": 7,
                 "long_stay_discount_percent": 15, "image_urls": []}
    MOCK_BOOKED_RANGES = []
    DIRECT_BOOKING_BENEFIT = "nessuna commissione di intermediazione"
    OWNER_INFO = {"name": "Proprietario"}
    OPENAI_API_KEY = "your_key"
    GEMINI_API_KEY = "your_key"

# Rilevamento della chiave API da utilizzare
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY or API_KEY == "your_gemini_api_key_here":
    API_KEY = os.getenv("OPENAI_API_KEY")
    if not API_KEY or API_KEY == "your_openai_api_key_here":
        if 'GEMINI_API_KEY' in globals() and GEMINI_API_KEY and GEMINI_API_KEY != "your_key" and GEMINI_API_KEY != "your_gemini_api_key_here":
            API_KEY = GEMINI_API_KEY
        else:
            API_KEY = OPENAI_API_KEY

# Configurazione Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AI-BOT-GittyStella")

app = FastAPI(
    title="AI Booking Assistant - Gitty&Stella",
    description="Prototipo di backend per il risponditore automatico WhatsApp dell'appartamento Gitty&Stella (Via Sardegna, Oristano)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

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


def call_llm_with_fallback(messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, tool_choice: Optional[str] = None):
    models_to_try = [DEFAULT_MODEL]
    if IS_GEMINI:
        for m in ["gemini-2.0-flash", "gemini-1.5-flash"]:
            if m not in models_to_try:
                models_to_try.append(m)

    last_exception = None
    for model in models_to_try:
        try:
            logger.info(f"[LLM CALL] Provo con modello: {model}")
            kwargs = {"model": model, "messages": messages}
            if tools:
                kwargs["tools"] = tools
            if tool_choice:
                kwargs["tool_choice"] = tool_choice
            response = client.chat.completions.create(**kwargs)
            logger.info(f"[LLM CALL] Chiamata riuscita con modello: {model}")
            return response
        except Exception as e:
            logger.warning(f"[LLM CALL] Errore con modello {model}: {e}")
            last_exception = e

    if last_exception:
        raise last_exception
    raise Exception("Tutti i tentativi di chiamata LLM sono falliti.")


# --- STATO IN MEMORIA (mock, si azzera ad ogni restart o su /api/reset) ---
booking_requests_db: List[Dict[str, Any]] = []
owner_notifications_db: List[Dict[str, Any]] = []
chat_sessions: Dict[str, List[Dict[str, Any]]] = {}
booking_flow_sessions: Dict[str, Dict[str, Any]] = {}
_last_known_lang: Dict[str, str] = {}

# --- MODELLI PYDANTIC ---
class MessageInput(BaseModel):
    user_id: str
    message: str
    user_name: Optional[str] = "Ospite"


class BookingRequestInput(BaseModel):
    guest_name: str
    guest_email: str
    guest_phone: str
    checkin: str
    checkout: str
    guests: int
    notes: Optional[str] = ""


# --- LOGICA DI DOMINIO (mock: nessun PMS reale, nessuna prenotazione confermata automaticamente) ---

def _dates_overlap(a_start: str, a_end: str, b_start: str, b_end: str) -> bool:
    a1, a2 = datetime.strptime(a_start, "%Y-%m-%d"), datetime.strptime(a_end, "%Y-%m-%d")
    b1, b2 = datetime.strptime(b_start, "%Y-%m-%d"), datetime.strptime(b_end, "%Y-%m-%d")
    return a1 < b2 and b1 < a2


def check_availability(checkin: str, checkout: str, guests: int) -> Dict[str, Any]:
    logger.info(f"[AVAILABILITY] Controllo {checkin} -> {checkout} per {guests} ospiti.")
    try:
        d1 = datetime.strptime(checkin, "%Y-%m-%d")
        d2 = datetime.strptime(checkout, "%Y-%m-%d")
        nights = (d2 - d1).days
        if nights <= 0:
            return {"available": False, "reason": "Le date di check-out devono essere successive al check-in."}
    except Exception:
        return {"available": False, "reason": "Formato data non valido, usa YYYY-MM-DD."}

    if guests > APARTMENT["max_occupancy"]:
        return {"available": False, "reason": f"L'appartamento ospita al massimo {APARTMENT['max_occupancy']} persone."}

    for occupied in MOCK_BOOKED_RANGES:
        if _dates_overlap(checkin, checkout, occupied["checkin"], occupied["checkout"]):
            return {"available": False, "reason": "Le date richieste sono già occupate. Provo a proporre date alternative vicine."}

    total_price = APARTMENT["base_price_per_night"] * nights
    discount_applied = False
    if nights >= APARTMENT["long_stay_discount_threshold_nights"]:
        discount = total_price * (APARTMENT["long_stay_discount_percent"] / 100)
        total_price -= discount
        discount_applied = True

    return {
        "available": True,
        "nights": nights,
        "price_per_night": APARTMENT["base_price_per_night"],
        "total_price": round(total_price, 2),
        "long_stay_discount_applied": discount_applied,
        "cleaning_fee": APARTMENT.get("cleaning_fee", 0),
        "benefit": DIRECT_BOOKING_BENEFIT,
        "image_url": APARTMENT["image_urls"][0] if APARTMENT.get("image_urls") else None,
    }


def create_booking_request(data: BookingRequestInput) -> Dict[str, Any]:
    logger.info(f"[BOOKING REQUEST] Nuova richiesta da {data.guest_name} per {data.checkin} -> {data.checkout}")
    request_id = f"REQ-{int(datetime.now().timestamp())}"
    record = {
        "request_id": request_id,
        "guest_name": data.guest_name,
        "guest_email": data.guest_email,
        "guest_phone": data.guest_phone,
        "checkin": data.checkin,
        "checkout": data.checkout,
        "guests": data.guests,
        "notes": data.notes,
        "status": "PENDING_OWNER_CONFIRMATION",
        "created_at": datetime.now().isoformat(),
    }
    booking_requests_db.append(record)
    return record


def notify_owner(booking_request_id: str, summary: str) -> Dict[str, Any]:
    logger.warning(f"[OWNER NOTIFICATION] Nuova richiesta ({booking_request_id}) per {OWNER_INFO.get('name')}: {summary}")
    notification = {
        "notification_id": f"NOTIF-{int(datetime.now().timestamp())}",
        "booking_request_id": booking_request_id,
        "summary": summary,
        "channel": OWNER_INFO.get("notification_channel", "whatsapp_owner_mock"),
        "status": "unread",
        "created_at": datetime.now().isoformat(),
    }
    owner_notifications_db.append(notification)
    return notification


# --- TOOLS PER FUNCTION CALLING ---
TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "check_apartment_availability",
            "description": "Verifica se l'appartamento Gitty&Stella è disponibile per le date richieste e calcola il prezzo totale.",
            "parameters": {
                "type": "object",
                "properties": {
                    "checkin": {"type": "string", "description": "Data di check-in in formato YYYY-MM-DD"},
                    "checkout": {"type": "string", "description": "Data di check-out in formato YYYY-MM-DD"},
                    "guests": {"type": "integer", "description": "Numero totale di ospiti"}
                },
                "required": ["checkin", "checkout", "guests"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_booking_request",
            "description": "Crea una richiesta di prenotazione con i dati dell'ospite. NON è una prenotazione confermata: deve essere approvata dal proprietario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "guest_name": {"type": "string", "description": "Nome e cognome dell'ospite"},
                    "guest_email": {"type": "string", "description": "Email dell'ospite"},
                    "guest_phone": {"type": "string", "description": "Telefono dell'ospite"},
                    "checkin": {"type": "string", "description": "Data di check-in YYYY-MM-DD"},
                    "checkout": {"type": "string", "description": "Data di check-out YYYY-MM-DD"},
                    "guests": {"type": "integer", "description": "Numero di ospiti"},
                    "notes": {"type": "string", "description": "Eventuali richieste speciali"}
                },
                "required": ["guest_name", "guest_email", "guest_phone", "checkin", "checkout", "guests"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "notify_owner_new_request",
            "description": "Notifica il proprietario dell'appartamento che è arrivata una nuova richiesta di prenotazione da confermare. Va sempre invocato subito dopo create_booking_request.",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_request_id": {"type": "string", "description": "ID della richiesta di prenotazione da notificare"},
                    "summary": {"type": "string", "description": "Riepilogo sintetico della richiesta per il proprietario"}
                },
                "required": ["booking_request_id", "summary"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_human_handover",
            "description": "Richiede l'intervento del proprietario/gestore per richieste speciali, reclami, o quando l'ospite chiede esplicitamente di parlare con una persona.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "Motivo del passaggio a un operatore umano"}
                },
                "required": ["reason"]
            }
        }
    }
]

SYSTEM_PROMPT = f"""Sei l'assistente virtuale di "{APARTMENT['name']}", un accogliente appartamento per affitti brevi in {APARTMENT['address']}.

LINEE GUIDA COMPORTAMENTALI:
1. Tono: caldo, semplice, ospitale — come un padrone di casa premuroso, non come un concierge di hotel di lusso. Niente offerte di servizi che l'appartamento non ha (spa, ristorante interno, ecc.).
2. Lingua: rispondi sempre nella stessa lingua usata dall'ospite (italiano, inglese, tedesco o francese).
3. Prenotazione diretta: quando parli di prezzo o disponibilità, ricorda sempre con orgoglio il vantaggio della prenotazione diretta: {DIRECT_BOOKING_BENEFIT}.
4. Onestà: sii sempre chiaro che una richiesta di prenotazione NON è automaticamente confermata. Il proprietario la confermerà a breve. Non promettere mai una prenotazione come certa.
5. Disponibilità: per domande su date, prezzo o disponibilità usa lo strumento `check_apartment_availability`.
6. Prenotazione: se l'ospite vuole procedere, raccogli nome, email, telefono, date e numero di ospiti, poi usa `create_booking_request`. Subito dopo, invoca sempre `notify_owner_new_request` per avvisare il proprietario.
7. Operatore umano: se l'ospite è irritato, chiede condizioni speciali fuori standard, o chiede esplicitamente di parlare con una persona, usa `trigger_human_handover`.
8. Immagini: quando presenti disponibilità o descrivi l'appartamento, includi sempre un'immagine su una riga separata in sintassi markdown, ad esempio:
   ![Gitty&Stella]({APARTMENT['image_urls'][0] if APARTMENT.get('image_urls') else ''})
"""


def execute_tool_call(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    if name == "check_apartment_availability":
        result = check_availability(
            checkin=arguments["checkin"],
            checkout=arguments["checkout"],
            guests=arguments.get("guests", 2)
        )
        return {"status": "success", "availability": result}

    elif name == "create_booking_request":
        booking_data = BookingRequestInput(
            guest_name=arguments["guest_name"],
            guest_email=arguments["guest_email"],
            guest_phone=arguments["guest_phone"],
            checkin=arguments["checkin"],
            checkout=arguments["checkout"],
            guests=arguments.get("guests", 2),
            notes=arguments.get("notes", "")
        )
        result = create_booking_request(booking_data)
        return {"status": "success", "booking_request": result}

    elif name == "notify_owner_new_request":
        result = notify_owner(
            booking_request_id=arguments["booking_request_id"],
            summary=arguments["summary"]
        )
        return {"status": "success", "notification": result}

    elif name == "trigger_human_handover":
        logger.warning(f"[HANDOVER] Richiesto passaggio al proprietario. Motivo: {arguments['reason']}")
        return {
            "status": "handover_active",
            "message": "Il proprietario è stato avvisato e prenderà il controllo della conversazione a breve."
        }

    else:
        return {"status": "error", "message": f"Strumento {name} non supportato."}


# --- ENDPOINTS ---

@app.get("/")
def read_root():
    try:
        with open(os.path.join(BASE_DIR, "index.html"), encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except Exception as e:
        logger.error(f"Errore caricamento index.html: {e}")
        return HTMLResponse(content=f"<h1>{APARTMENT['name']} online</h1>", status_code=200)


@app.get("/i18n.js")
def get_i18n_js():
    return FileResponse(os.path.join(BASE_DIR, "i18n.js"), media_type="application/javascript")


@app.get("/api/apartment")
def get_apartment():
    return APARTMENT


@app.get("/api/booking-requests")
def get_booking_requests():
    return booking_requests_db


@app.get("/api/owner/notifications")
def get_owner_notifications():
    return owner_notifications_db


@app.post("/api/reset")
def reset_demo():
    booking_requests_db.clear()
    owner_notifications_db.clear()
    chat_sessions.clear()
    booking_flow_sessions.clear()
    _last_known_lang.clear()
    return {"status": "success", "message": "Demo azzerata con successo."}


@app.post("/webhook/whatsapp")
def whatsapp_webhook(input_data: MessageInput = Body(...)):
    user_id = input_data.user_id
    user_msg = input_data.message

    if user_id not in chat_sessions:
        chat_sessions[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    session_history = chat_sessions[user_id]
    session_history.append({"role": "user", "content": user_msg})

    try:
        is_valid_key = API_KEY.startswith("sk-") or API_KEY.startswith("AIzaSy") or IS_GEMINI
        if API_KEY in ["your_openai_api_key_here", "your_gemini_api_key_here", "your_key", ""] or not is_valid_key:
            logger.warning("[WARNING] API Key non configurata o non valida. Restituisco risposta mock.")
            return process_mock_response(user_msg, input_data.user_name, user_id)

        response = call_llm_with_fallback(
            messages=session_history,
            tools=TOOLS_DEFINITION,
            tool_choice="auto"
        )
        response_message = response.choices[0].message

        if response_message.tool_calls:
            session_history.append(response_message)
            tool_calls_data = []
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                tool_output = execute_tool_call(function_name, function_args)
                session_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(tool_output)
                })
                tool_calls_data.append({"name": function_name, "arguments": function_args})

            second_response = call_llm_with_fallback(messages=session_history)
            assistant_reply = second_response.choices[0].message.content
            session_history.append({"role": "assistant", "content": assistant_reply})

            is_handover = any(tc.function.name == "trigger_human_handover" for tc in response_message.tool_calls)

            return {
                "sender": f"{APARTMENT['name']} (AI Assistant)",
                "reply": assistant_reply,
                "session_active": not is_handover,
                "handover_triggered": is_handover,
                "tool_calls": tool_calls_data
            }
        else:
            assistant_reply = response_message.content
            session_history.append({"role": "assistant", "content": assistant_reply})
            return {
                "sender": f"{APARTMENT['name']} (AI Assistant)",
                "reply": assistant_reply,
                "session_active": True,
                "handover_triggered": False,
                "tool_calls": []
            }

    except Exception as e:
        logger.error(f"[ERROR] Errore nell'elaborazione del messaggio: {e}")
        return process_mock_response(user_msg, input_data.user_name, user_id)


# --- MOCK MULTILINGUA (nessuna chiave API richiesta per testare la demo) ---

_LANG_HINTS = {
    "de": ["verfügbar", "verfugbar", "buchen", "zimmer", "wohnung", "hallo", "bitte", "danke", "ich möchte"],
    "fr": ["disponible", "réserv", "reserv", "bonjour", "merci", "chambre", "appartement", "je voudrais", "svp",
           "avez-vous", "combien", "nuit", "pouvez-vous"],
    "en": ["availab", "book", "booking", "hello", "thanks", "apartment", "room", "price", "human", "person"],
    "it": ["disponibil", "prenot", "ciao", "buongiorno", "grazie", "camera", "appartamento", "prezzo", "umano", "persona"],
}

_INTENT_KEYWORDS = {
    "booking": ["prenot", "blocca", "book", "reserv", "réserv", "buchen"],
    "availability": ["disponibil", "availab", "opening", "vacan", "free date", "any date", "verfügbar", "verfugbar",
                      "camer", "stanz", "room", "zimmer", "chambre", "appartement",
                      "cost", "prezz", "price", "preis", "prix", "disponib"],
    "human": ["umano", "staff", "proprietario", "human", "mensch", "reception", "operatore", "lament", "complain",
              "parlare con", "talk to", "speak to", "sprechen mit", "parler à", "parler a"],
    "parking": ["parcheggi", "parking", "parkplatz"],
    "pets": ["animal", "cane", "cani", "gatto", "gatti", "pet", "hund", "katze", "katzen", "animaux", "chien", "chat"],
    "checkin_time": ["orario", "check-in", "checkin", "arriv", "ankunft", "arrivée", "arrivee"],
    "deposit": ["caparra", "cauzion", "deposit", "kaution", "dépôt", "depot", "acompte"],
    "tourist_tax": ["tassa di soggiorno", "tourist tax", "kurtaxe", "taxe de séjour", "taxe de sejour"],
    "id_document": ["documento", "carta d'identit", "passaport", "id document", "ausweis", "pièce d'identité", "piece d'identite", "alloggiati"],
    "wifi": ["wifi", "wi-fi", "internet", "wlan"],
    "cancellation": ["cancell", "disdett", "rimbors", "cancel", "refund", "storn", "annull"],
}

_AFFIRMATIVE = {
    "it": ["si", "sì", "ok", "va bene", "confermo", "certo", "perfetto", "procedi", "esatto"],
    "en": ["yes", "yeah", "yep", "ok", "okay", "sure", "confirm", "go ahead", "correct"],
    "de": ["ja", "okay", "ok", "klar", "passt", "genau"],
    "fr": ["oui", "ok", "d'accord", "daccord", "confirme", "exact"],
}
_NEGATIVE = {
    "it": ["no", "annulla", "niente", "lascia stare", "non ora"],
    "en": ["no", "not now", "cancel", "nevermind", "never mind"],
    "de": ["nein", "abbrechen", "nicht jetzt"],
    "fr": ["non", "annule", "pas maintenant"],
}
_ABORT_KEYWORDS = ["annulla", "cancel", "stop", "basta", "lascia stare", "forget it", "nevermind",
                    "vergiss es", "laisse tomber", "oublie"]

_MONTHS = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6,
    "luglio": 7, "agosto": 8, "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "mai": 5, "juni": 6, "juli": 7,
    "oktober": 10, "dezember": 12,
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "juin": 6,
    "juillet": 7, "août": 8, "aout": 8, "décembre": 12, "decembre": 12,
}

_MOCK_REPLIES = {
    "it": {
        "greeting": "Ciao {name}! Sono l'assistente virtuale di Gitty&Stella, il nostro appartamento in Via Sardegna a Oristano. Posso dirti subito la disponibilità e il prezzo per le tue date, oppure raccontarti la zona. Come posso aiutarti?",
        "human": "Capisco {name}. Ho avvisato il proprietario: ti risponderà personalmente a breve su questo stesso canale.",
        "ask_checkin": "Perfetto! Da quale data vorresti arrivare? (es. 22/08/2026 o 22 agosto)",
        "ask_checkout": "E fino a quando vorresti restare? (data di check-out)",
        "ask_guests": "Per quante persone?",
        "availability_ok": "Ottima notizia: per queste date l'appartamento è disponibile! 🏡\nPrezzo: **{total}€** per {nights} {nights_label} ({price}€/notte), prenotando direttamente ottieni {benefit}.\n\n![Gitty&Stella]({image})\n\nVuoi che inoltri la tua richiesta di prenotazione al proprietario? (sì/no)",
        "availability_ko": "Mi dispiace, per queste date non c'è disponibilità: {reason}\nVuoi provare con altre date?",
        "proceed_declined": "Nessun problema! Se vuoi controllare altre date scrivimi pure quando vuoi 😊",
        "ask_name": "Perfetto! Come ti chiami? (nome e cognome)",
        "ask_email": "Grazie {name}! Qual è la tua email?",
        "ask_phone": "E il tuo numero di telefono?",
        "ask_confirm": "Riepilogo della richiesta:\n📅 {checkin} → {checkout} ({nights} {nights_label})\n👥 {guests} ospiti\n💶 Totale: {total}€\n👤 {name}, {email}, {phone}\n\nConfermi l'invio della richiesta al proprietario? (sì/no)",
        "booking_confirmed": "Fatto! Ho inviato la tua richiesta al proprietario (codice **{request_id}**). Non è ancora una prenotazione confermata: riceverai una risposta appena il proprietario avrà verificato tutto, di solito entro poche ore. 📩\n\n![Gitty&Stella]({image})",
        "booking_cancelled": "Va bene, ho annullato la richiesta. Se vuoi ricominciare scrivimi pure quando vuoi!",
        "invalid_date": "Non sono riuscito a capire la data — puoi scriverla ad esempio così: 22/08/2026 oppure 22 agosto?",
        "checkout_before_checkin": "La data di partenza deve essere successiva al check-in che mi hai indicato ({checkin}). Quale data di check-out preferisci?",
        "invalid_guests": "Puoi indicarmi il numero di ospiti in cifre? Es. 2",
        "please_yes_no": "Rispondi 'sì' o 'no', per favore 🙂",
        "parking": "Sì, è disponibile un parcheggio gratuito nelle vicinanze (dettagli da confermare).",
        "pets": "Gli animali sono ammessi su richiesta: scrivici prima di prenotare per verificare la disponibilità.",
        "checkin_time": "Il check-in è autonomo e con orario flessibile: ti invieremo tutte le istruzioni via WhatsApp prima del tuo arrivo.",
        "deposit": "Sì, di solito è richiesta una piccola cauzione (importo da confermare), restituita al check-out.",
        "tourist_tax": "Sì, la tassa di soggiorno comunale si paga in loco, per persona a notte (importo da confermare con il Comune di Oristano).",
        "id_document": "Sì: per legge registriamo i dati di tutti gli ospiti maggiorenni entro 24 ore dall'arrivo (Alloggiati Web, Polizia di Stato).",
        "wifi": "Sì, il WiFi è incluso gratuitamente in tutto l'appartamento.",
        "cancellation": "La cancellazione è flessibile fino a pochi giorni prima dell'arrivo (condizioni dettagliate in fase di conferma).",
    },
    "en": {
        "greeting": "Hi {name}! I'm the virtual assistant for Gitty&Stella, our apartment on Via Sardegna in Oristano. I can check availability and price for your dates, or tell you about the area. How can I help?",
        "human": "I understand, {name}. I've notified the owner — they'll get back to you personally on this same channel shortly.",
        "ask_checkin": "Great! What's your check-in date? (e.g. 22/08/2026 or August 22)",
        "ask_checkout": "And until when would you like to stay? (check-out date)",
        "ask_guests": "For how many guests?",
        "availability_ok": "Good news — the apartment is available for those dates! 🏡\nPrice: **€{total}** for {nights} {nights_label} (€{price}/night), booking directly gets you {benefit}.\n\n![Gitty&Stella]({image})\n\nShould I forward your booking request to the owner? (yes/no)",
        "availability_ko": "Sorry, those dates aren't available: {reason}\nWant to try different dates?",
        "proceed_declined": "No problem! Feel free to check other dates whenever you like 😊",
        "ask_name": "Great! What's your name? (first and last name)",
        "ask_email": "Thanks {name}! What's your email?",
        "ask_phone": "And your phone number?",
        "ask_confirm": "Request summary:\n📅 {checkin} → {checkout} ({nights} {nights_label})\n👥 {guests} guests\n💶 Total: €{total}\n👤 {name}, {email}, {phone}\n\nShall I send the request to the owner? (yes/no)",
        "booking_confirmed": "Done! I've sent your request to the owner (code **{request_id}**). This isn't a confirmed booking yet: you'll get a reply once the owner checks everything, usually within a few hours. 📩\n\n![Gitty&Stella]({image})",
        "booking_cancelled": "Alright, I've cancelled the request. Message me anytime if you'd like to start again!",
        "invalid_date": "I couldn't understand that date — could you write it like this: 22/08/2026 or August 22?",
        "checkout_before_checkin": "The check-out date must be after the check-in you gave me ({checkin}). Which check-out date would you like?",
        "invalid_guests": "Could you tell me the number of guests as a number? E.g. 2",
        "please_yes_no": "Please reply 'yes' or 'no' 🙂",
        "parking": "Yes, free parking is available nearby (details to be confirmed).",
        "pets": "Pets are allowed on request: message us before booking to check availability.",
        "checkin_time": "Check-in is self-service with flexible timing: we'll send all instructions on WhatsApp before your arrival.",
        "deposit": "Yes, a small deposit is usually required (amount to be confirmed), refunded at check-out.",
        "tourist_tax": "Yes, the municipal tourist tax is paid on site, per person per night (amount to be confirmed with the Municipality of Oristano).",
        "id_document": "Yes: by law we register all adult guests' details within 24 hours of arrival (Alloggiati Web, State Police).",
        "wifi": "Yes, WiFi is included for free throughout the apartment.",
        "cancellation": "Cancellation is flexible up to a few days before arrival (detailed conditions pending confirmation).",
    },
    "de": {
        "greeting": "Hallo {name}! Ich bin der virtuelle Assistent von Gitty&Stella, unserer Wohnung in der Via Sardegna in Oristano. Ich kann dir sofort Verfügbarkeit und Preis nennen. Wie kann ich helfen?",
        "human": "Verstehe, {name}. Ich habe den Eigentümer informiert — er meldet sich in Kürze persönlich auf diesem Kanal.",
        "ask_checkin": "Perfekt! Ab welchem Datum möchtest du anreisen? (z.B. 22.08.2026 oder 22. August)",
        "ask_checkout": "Und bis wann möchtest du bleiben? (Abreisedatum)",
        "ask_guests": "Für wie viele Personen?",
        "availability_ok": "Gute Nachricht — die Wohnung ist für diese Termine verfügbar! 🏡\nPreis: **{total}€** für {nights} {nights_label} ({price}€/Nacht), bei Direktbuchung erhältst du {benefit}.\n\n![Gitty&Stella]({image})\n\nSoll ich deine Buchungsanfrage an den Eigentümer weiterleiten? (ja/nein)",
        "availability_ko": "Leider ist für diese Termine nichts frei: {reason}\nMöchtest du andere Termine versuchen?",
        "proceed_declined": "Kein Problem! Frag gerne jederzeit nach anderen Terminen 😊",
        "ask_name": "Perfekt! Wie heißt du? (Vor- und Nachname)",
        "ask_email": "Danke {name}! Wie ist deine E-Mail-Adresse?",
        "ask_phone": "Und deine Telefonnummer?",
        "ask_confirm": "Zusammenfassung der Anfrage:\n📅 {checkin} → {checkout} ({nights} {nights_label})\n👥 {guests} Gäste\n💶 Gesamt: {total}€\n👤 {name}, {email}, {phone}\n\nSoll ich die Anfrage an den Eigentümer senden? (ja/nein)",
        "booking_confirmed": "Erledigt! Ich habe deine Anfrage an den Eigentümer gesendet (Code **{request_id}**). Das ist noch keine bestätigte Buchung: du erhältst eine Antwort, sobald der Eigentümer alles geprüft hat, meist innerhalb weniger Stunden. 📩\n\n![Gitty&Stella]({image})",
        "booking_cancelled": "Alles klar, ich habe die Anfrage abgebrochen. Schreib mir jederzeit, wenn du neu beginnen möchtest!",
        "invalid_date": "Ich konnte das Datum nicht verstehen — kannst du es so schreiben: 22.08.2026 oder 22. August?",
        "checkout_before_checkin": "Das Abreisedatum muss nach dem angegebenen Check-in ({checkin}) liegen. Welches Abreisedatum möchtest du?",
        "invalid_guests": "Kannst du mir die Anzahl der Gäste als Zahl nennen? Z.B. 2",
        "please_yes_no": "Bitte antworte mit 'ja' oder 'nein' 🙂",
        "parking": "Ja, in der Nähe steht ein kostenloser Parkplatz zur Verfügung (Details werden noch bestätigt).",
        "pets": "Haustiere sind auf Anfrage erlaubt: schreib uns vor der Buchung, um die Verfügbarkeit zu prüfen.",
        "checkin_time": "Der Check-in erfolgt selbstständig mit flexibler Uhrzeit: wir senden dir alle Anweisungen vor deiner Ankunft per WhatsApp.",
        "deposit": "Ja, meist wird eine kleine Kaution verlangt (Betrag noch zu bestätigen), die beim Check-out zurückerstattet wird.",
        "tourist_tax": "Ja, die kommunale Kurtaxe wird vor Ort bezahlt, pro Person und Nacht (Betrag noch mit der Gemeinde Oristano zu bestätigen).",
        "id_document": "Ja: gesetzlich registrieren wir die Daten aller erwachsenen Gäste innerhalb von 24 Stunden nach Ankunft (Alloggiati Web, Staatspolizei).",
        "wifi": "Ja, WLAN ist in der gesamten Wohnung kostenlos inbegriffen.",
        "cancellation": "Die Stornierung ist flexibel bis wenige Tage vor der Anreise (detaillierte Bedingungen werden noch bestätigt).",
    },
    "fr": {
        "greeting": "Bonjour {name} ! Je suis l'assistant virtuel de Gitty&Stella, notre appartement Via Sardegna à Oristano. Je peux vérifier la disponibilité et le prix pour vos dates. Comment puis-je vous aider ?",
        "human": "Je comprends, {name}. J'ai informé le propriétaire — il vous répondra personnellement très bientôt sur ce même canal.",
        "ask_checkin": "Parfait ! À partir de quelle date voudriez-vous arriver ? (ex. 22/08/2026 ou 22 août)",
        "ask_checkout": "Et jusqu'à quand souhaitez-vous rester ? (date de départ)",
        "ask_guests": "Pour combien de personnes ?",
        "availability_ok": "Bonne nouvelle — l'appartement est disponible pour ces dates ! 🏡\nPrix : **{total}€** pour {nights} {nights_label} ({price}€/nuit), en réservant directement vous bénéficiez de {benefit}.\n\n![Gitty&Stella]({image})\n\nSouhaitez-vous que je transmette votre demande au propriétaire ? (oui/non)",
        "availability_ko": "Désolé, ces dates ne sont pas disponibles : {reason}\nVoulez-vous essayer d'autres dates ?",
        "proceed_declined": "Aucun problème ! N'hésitez pas à demander d'autres dates quand vous le souhaitez 😊",
        "ask_name": "Parfait ! Quel est votre nom ? (nom et prénom)",
        "ask_email": "Merci {name} ! Quelle est votre adresse email ?",
        "ask_phone": "Et votre numéro de téléphone ?",
        "ask_confirm": "Récapitulatif de la demande :\n📅 {checkin} → {checkout} ({nights} {nights_label})\n👥 {guests} personnes\n💶 Total : {total}€\n👤 {name}, {email}, {phone}\n\nDois-je envoyer la demande au propriétaire ? (oui/non)",
        "booking_confirmed": "C'est fait ! J'ai envoyé votre demande au propriétaire (code **{request_id}**). Ce n'est pas encore une réservation confirmée : vous recevrez une réponse dès que le propriétaire aura tout vérifié, généralement en quelques heures. 📩\n\n![Gitty&Stella]({image})",
        "booking_cancelled": "D'accord, j'ai annulé la demande. Écrivez-moi quand vous voulez pour recommencer !",
        "invalid_date": "Je n'ai pas compris cette date — pouvez-vous l'écrire ainsi : 22/08/2026 ou 22 août ?",
        "checkout_before_checkin": "La date de départ doit être postérieure au check-in indiqué ({checkin}). Quelle date de départ souhaitez-vous ?",
        "invalid_guests": "Pouvez-vous m'indiquer le nombre de personnes en chiffre ? Ex. 2",
        "please_yes_no": "Merci de répondre 'oui' ou 'non' 🙂",
        "parking": "Oui, un parking gratuit est disponible à proximité (détails à confirmer).",
        "pets": "Les animaux sont admis sur demande : écrivez-nous avant de réserver pour vérifier la disponibilité.",
        "checkin_time": "Le check-in est autonome avec horaire flexible : nous vous envoyons toutes les instructions sur WhatsApp avant votre arrivée.",
        "deposit": "Oui, une petite caution est généralement demandée (montant à confirmer), restituée au départ.",
        "tourist_tax": "Oui, la taxe de séjour communale se paie sur place, par personne et par nuit (montant à confirmer avec la Commune d'Oristano).",
        "id_document": "Oui : la loi nous oblige à enregistrer les données de tous les hôtes majeurs dans les 24h suivant l'arrivée (Alloggiati Web, police d'État).",
        "wifi": "Oui, le WiFi est inclus gratuitement dans tout l'appartement.",
        "cancellation": "L'annulation est flexible jusqu'à quelques jours avant l'arrivée (conditions détaillées en attente de confirmation).",
    },
}


def _starts_word(msg_low: str, kw: str) -> bool:
    """Vero se kw compare a inizio parola in msg_low (kw può essere il prefisso di una parola più lunga,
    es. 'prenot' in 'prenotare'). Evita falsi positivi come 'hi' dentro 'chiamo' o 'richiesta'."""
    return re.search(r"(?:^|[^a-zà-ÿ])" + re.escape(kw), msg_low) is not None


def _detect_lang_scored(msg: str) -> "tuple[Optional[str], int]":
    """Rileva la lingua e restituisce anche il punteggio di confidenza: se il punteggio è 0
    (nessuna parola chiave riconosciuta) il chiamante può decidere di ricadere sull'ultima
    lingua nota della conversazione invece di assumere sempre l'italiano."""
    msg_low = msg.lower()
    scores = {lang: sum(1 for kw in kws if _starts_word(msg_low, kw)) for lang, kws in _LANG_HINTS.items()}
    best_score = max(scores.values())
    if best_score == 0:
        return None, 0
    tied = [lang for lang, score in scores.items() if score == best_score]
    # In caso di pareggio (es. radici condivise tra lingue latine) preferiamo l'italiano,
    # lingua predefinita dell'appartamento, invece di dipendere dall'ordine del dizionario.
    return ("it" if "it" in tied else tied[0]), best_score


def _detect_lang(msg: str) -> str:
    lang, _ = _detect_lang_scored(msg)
    return lang or "it"


def _detect_intent(msg: str) -> str:
    msg_low = msg.lower()
    for intent, kws in _INTENT_KEYWORDS.items():
        if any(_starts_word(msg_low, kw) for kw in kws):
            return intent
    return "greeting"


def _is_affirmative(text: str, lang: str) -> bool:
    t = f" {text.lower().strip()} "
    return any(t.startswith(f" {w}") or f" {w} " in t for w in _AFFIRMATIVE.get(lang, _AFFIRMATIVE["it"]))


def _is_negative(text: str, lang: str) -> bool:
    t = f" {text.lower().strip()} "
    return any(t.startswith(f" {w}") or f" {w} " in t for w in _NEGATIVE.get(lang, _NEGATIVE["it"]))


def _is_abort(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in _ABORT_KEYWORDS)


def _find_dates(text: str) -> List[str]:
    """Estrae date in formato YYYY-MM-DD da testo libero multilingua (numeriche o con nome del mese,
    sia in ordine giorno-mese "22 agosto" che mese-giorno "August 22nd", con o senza suffissi ordinali)."""
    text_low = re.sub(r"\b(\d{1,2})(st|nd|rd|th)\b", r"\1", text.lower())
    now = datetime.now()
    found = []

    month_pattern = "|".join(sorted(_MONTHS.keys(), key=len, reverse=True))

    # Pattern "dal X al Y <mese>" / "from X to Y <month>" / "vom X bis Y <Monat>" / "du X au Y <mois>"
    range_match = re.search(
        rf"(?:dal|from|vom|du)\s+(\d{{1,2}})\.?\s*(?:al|to|bis|au)\s+(\d{{1,2}})\.?\s+({month_pattern})\.?\s*(\d{{4}})?",
        text_low
    )
    if range_match:
        d1, d2, month_name, year_str = range_match.groups()
        mo = _MONTHS[month_name]
        year = int(year_str) if year_str else now.year
        for d in (d1, d2):
            try:
                dt = datetime(year, mo, int(d))
                if year_str is None and dt.date() < now.date():
                    dt = datetime(year + 1, mo, int(d))
                found.append((range_match.start(), dt))
            except ValueError:
                continue
        if found:
            found.sort(key=lambda r: r[0])
            return [d.strftime("%Y-%m-%d") for _, d in found]

    positions = []
    for m in re.finditer(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", text_low):
        y, mo, d = map(int, m.groups())
        positions.append((m.start(), y, mo, d))
    for m in re.finditer(r"\b(\d{1,2})[/.](\d{1,2})[/.](\d{4})\b", text_low):
        d, mo, y = map(int, m.groups())
        positions.append((m.start(), y, mo, d))
    for m in re.finditer(rf"\b(\d{{1,2}})\s+({month_pattern})\.?\s*(\d{{4}})?\b", text_low):
        d = int(m.group(1))
        mo = _MONTHS[m.group(2)]
        y = int(m.group(3)) if m.group(3) else None
        positions.append((m.start(), y, mo, d))
    # Ordine inglese "month day[, year]", es. "August 22" o "August 22, 2026"
    for m in re.finditer(rf"\b({month_pattern})\.?\s+(\d{{1,2}})\b,?\s*(\d{{4}})?", text_low):
        mo = _MONTHS[m.group(1)]
        d = int(m.group(2))
        y = int(m.group(3)) if m.group(3) else None
        positions.append((m.start(), y, mo, d))

    positions.sort(key=lambda r: r[0])
    for _, y, mo, d in positions:
        try:
            if y is None:
                y = now.year
                candidate = datetime(y, mo, d)
                if candidate.date() < now.date():
                    y += 1
            found.append((0, datetime(y, mo, d)))
        except ValueError:
            continue
    return [d.strftime("%Y-%m-%d") for _, d in found]


def _find_guest_count(text: str) -> Optional[int]:
    """Estrae il numero di ospiti solo se accompagnato da una parola chiave (persone/guests/...),
    per non confondere un numero di ospiti con un giorno del mese in una frase come '22 agosto'."""
    m = re.search(r"\b(\d{1,2})\s*(persone|persona|ospiti|guests?|people|personen|g[äa]ste|personnes)\b", text.lower())
    return int(m.group(1)) if m else None


def _find_guest_count_loose(text: str) -> Optional[int]:
    """Come _find_guest_count, ma con fallback su un numero isolato: da usare SOLO quando l'intero
    messaggio è la risposta diretta alla domanda 'per quante persone?'."""
    strict = _find_guest_count(text)
    if strict:
        return strict
    m = re.search(r"\b(\d{1,2})\b", text)
    return int(m.group(1)) if m else None


def _apartment_image() -> str:
    return APARTMENT["image_urls"][0] if APARTMENT.get("image_urls") else ""


_NIGHTS_LABEL = {
    "it": ("notte", "notti"), "en": ("night", "nights"),
    "de": ("Nacht", "Nächte"), "fr": ("nuit", "nuits"),
}

# Traduzione del vantaggio "prenotazione diretta" per il motore mock (il DIRECT_BOOKING_BENEFIT
# di config.py resta in italiano perché usato anche nel system prompt del vero LLM, che lo
# riformula da solo nella lingua dell'utente; il mock invece inserisce il testo alla lettera).
_BENEFIT_TEXT = {
    "it": "nessuna commissione di intermediazione, prezzo netto e risposta rapida via WhatsApp",
    "en": "no intermediary commission, a net price, and a fast reply on WhatsApp",
    "de": "keine Vermittlungsprovision, Nettopreis und eine schnelle Antwort auf WhatsApp",
    "fr": "aucune commission d'intermédiaire, un prix net et une réponse rapide sur WhatsApp",
}


def _nights_label(nights: int, lang: str) -> str:
    singular, plural = _NIGHTS_LABEL.get(lang, _NIGHTS_LABEL["it"])
    return singular if nights == 1 else plural


def _next_missing_field(flow: Dict[str, Any]) -> str:
    for field in ("checkin", "checkout", "guests"):
        if not flow.get(field):
            return field
    return "proceed"


def _prompt_for_field(field: str, replies: Dict[str, str]) -> str:
    return {"checkin": replies["ask_checkin"], "checkout": replies["ask_checkout"], "guests": replies["ask_guests"]}[field]


def _run_availability_step(flow: Dict[str, Any], replies: Dict[str, str]) -> Dict[str, Any]:
    """Calcola la disponibilità per i dati raccolti finora e prepara la risposta + prossimo stage del flow."""
    availability = check_availability(flow["checkin"], flow["checkout"], flow["guests"])
    if not availability.get("available"):
        flow["checkin"] = None
        flow["checkout"] = None
        flow["guests"] = None
        flow["stage"] = "checkin"
        return {
            "reply": replies["availability_ko"].format(reason=availability.get("reason", "")),
            "tool_calls": [{"name": "check_apartment_availability", "arguments": {"checkin": flow.get("checkin"), "checkout": flow.get("checkout"), "guests": flow.get("guests")}}],
        }

    flow["stage"] = "proceed"
    flow["last_availability"] = availability
    reply = replies["availability_ok"].format(
        total=availability["total_price"], nights=availability["nights"], price=availability["price_per_night"],
        nights_label=_nights_label(availability["nights"], flow["lang"]),
        benefit=_BENEFIT_TEXT.get(flow["lang"], _BENEFIT_TEXT["it"]), image=_apartment_image()
    )
    return {
        "reply": reply,
        "tool_calls": [{"name": "check_apartment_availability", "arguments": {"checkin": flow["checkin"], "checkout": flow["checkout"], "guests": flow["guests"]}}],
    }


def _advance_flow(flow: Dict[str, Any], replies: Dict[str, str]) -> Dict[str, Any]:
    """Dopo aver aggiornato un campo del flow, decide se chiedere il prossimo dato o calcolare la disponibilità."""
    missing = _next_missing_field(flow)
    if missing != "proceed":
        flow["stage"] = missing
        return {"reply": _prompt_for_field(missing, replies), "tool_calls": []}
    return _run_availability_step(flow, replies)


def process_mock_response(user_msg: str, user_name: str, user_id: str) -> Dict[str, Any]:
    flow = booking_flow_sessions.get(user_id)

    # Un utente può chiedere di parlare con una persona in qualsiasi momento, anche a metà del flow.
    if _detect_intent(user_msg) == "human":
        lang = flow["lang"] if flow else (_detect_lang_scored(user_msg)[0] or _last_known_lang.get(user_id, "it"))
        booking_flow_sessions.pop(user_id, None)
        return {
            "sender": f"{APARTMENT['name']} (AI Assistant - Mock Engine)",
            "reply": _MOCK_REPLIES.get(lang, _MOCK_REPLIES["it"])["human"].format(name=user_name),
            "session_active": False,
            "handover_triggered": True,
            "tool_calls": [{"name": "trigger_human_handover", "arguments": {"reason": "Richiesta esplicita di un operatore umano"}}],
        }

    if flow and _is_abort(user_msg):
        lang = flow["lang"]
        booking_flow_sessions.pop(user_id, None)
        return {
            "sender": f"{APARTMENT['name']} (AI Assistant - Mock Engine)",
            "reply": _MOCK_REPLIES.get(lang, _MOCK_REPLIES["it"])["booking_cancelled"],
            "session_active": True, "handover_triggered": False, "tool_calls": [],
        }

    if flow:
        lang = flow["lang"]
        replies = _MOCK_REPLIES.get(lang, _MOCK_REPLIES["it"])
        stage = flow["stage"]
        tool_calls: List[Dict[str, Any]] = []

        if stage == "checkin":
            dates = _find_dates(user_msg)
            if not dates:
                result = {"reply": replies["invalid_date"], "tool_calls": []}
            else:
                flow["checkin"] = dates[0]
                if len(dates) > 1:
                    flow["checkout"] = dates[1]
                result = _advance_flow(flow, replies)

        elif stage == "checkout":
            dates = _find_dates(user_msg)
            if not dates:
                result = {"reply": replies["invalid_date"], "tool_calls": []}
            else:
                # Se l'utente ripete anche la data di arrivo, prendiamo l'ultima data indicata come partenza.
                candidate_checkout = dates[-1]
                if candidate_checkout <= flow["checkin"]:
                    result = {"reply": replies["checkout_before_checkin"].format(checkin=flow["checkin"]), "tool_calls": []}
                else:
                    flow["checkout"] = candidate_checkout
                    result = _advance_flow(flow, replies)

        elif stage == "guests":
            guests = _find_guest_count_loose(user_msg)
            if not guests or guests < 1:
                result = {"reply": replies["invalid_guests"], "tool_calls": []}
            else:
                flow["guests"] = guests
                result = _advance_flow(flow, replies)

        elif stage == "proceed":
            if _is_affirmative(user_msg, lang):
                flow["stage"] = "name"
                result = {"reply": replies["ask_name"], "tool_calls": []}
            elif _is_negative(user_msg, lang):
                booking_flow_sessions.pop(user_id, None)
                result = {"reply": replies["proceed_declined"], "tool_calls": []}
            else:
                result = {"reply": replies["please_yes_no"], "tool_calls": []}

        elif stage == "name":
            flow["name"] = user_msg.strip()
            flow["stage"] = "email"
            result = {"reply": replies["ask_email"].format(name=flow["name"]), "tool_calls": []}

        elif stage == "email":
            flow["email"] = user_msg.strip()
            flow["stage"] = "phone"
            result = {"reply": replies["ask_phone"], "tool_calls": []}

        elif stage == "phone":
            flow["phone"] = user_msg.strip()
            flow["stage"] = "confirm"
            avail = flow["last_availability"]
            result = {
                "reply": replies["ask_confirm"].format(
                    checkin=flow["checkin"], checkout=flow["checkout"], nights=avail["nights"],
                    nights_label=_nights_label(avail["nights"], lang),
                    guests=flow["guests"], total=avail["total_price"],
                    name=flow["name"], email=flow["email"], phone=flow["phone"]
                ),
                "tool_calls": [],
            }

        elif stage == "confirm":
            if _is_affirmative(user_msg, lang):
                booking_data = BookingRequestInput(
                    guest_name=flow["name"], guest_email=flow["email"], guest_phone=flow["phone"],
                    checkin=flow["checkin"], checkout=flow["checkout"], guests=flow["guests"], notes=""
                )
                record = create_booking_request(booking_data)
                notify_owner(record["request_id"], f"Richiesta da {flow['name']} per {flow['checkin']} -> {flow['checkout']} ({flow['guests']} ospiti)")
                booking_flow_sessions.pop(user_id, None)
                result = {
                    "reply": replies["booking_confirmed"].format(request_id=record["request_id"], image=_apartment_image()),
                    "tool_calls": [
                        {"name": "create_booking_request", "arguments": {"guest_name": booking_data.guest_name, "checkin": booking_data.checkin, "checkout": booking_data.checkout}},
                        {"name": "notify_owner_new_request", "arguments": {"booking_request_id": record["request_id"]}},
                    ],
                }
            elif _is_negative(user_msg, lang):
                booking_flow_sessions.pop(user_id, None)
                result = {"reply": replies["booking_cancelled"], "tool_calls": []}
            else:
                result = {"reply": replies["please_yes_no"], "tool_calls": []}
        else:
            booking_flow_sessions.pop(user_id, None)
            result = {"reply": replies["greeting"].format(name=user_name), "tool_calls": []}

        return {
            "sender": f"{APARTMENT['name']} (AI Assistant - Mock Engine)",
            "reply": result["reply"],
            "session_active": True,
            "handover_triggered": False,
            "tool_calls": result["tool_calls"],
        }

    # Nessun flow attivo: rileviamo lingua e intento dal messaggio.
    # Se il messaggio non contiene segnali di lingua chiari (es. "yes", numeri, frasi ambigue),
    # ricadiamo sull'ultima lingua nota della conversazione invece di assumere sempre l'italiano.
    detected_lang, _ = _detect_lang_scored(user_msg)
    lang = detected_lang or _last_known_lang.get(user_id, "it")
    _last_known_lang[user_id] = lang
    intent = _detect_intent(user_msg)
    replies = _MOCK_REPLIES.get(lang, _MOCK_REPLIES["it"])

    if intent in ("booking", "availability"):
        new_flow = {"lang": lang, "stage": "checkin", "checkin": None, "checkout": None, "guests": None,
                    "name": None, "email": None, "phone": None, "last_availability": None}
        dates = _find_dates(user_msg)
        if dates:
            new_flow["checkin"] = dates[0]
            if len(dates) > 1:
                new_flow["checkout"] = dates[1]
        guests = _find_guest_count(user_msg)
        if guests:
            new_flow["guests"] = guests
        booking_flow_sessions[user_id] = new_flow
        result = _advance_flow(new_flow, replies)
        reply, tool_calls = result["reply"], result["tool_calls"]
    elif intent == "human":
        reply = replies["human"].format(name=user_name)
        tool_calls = [{"name": "trigger_human_handover", "arguments": {"reason": "Richiesta esplicita di un operatore umano"}}]
        return {
            "sender": f"{APARTMENT['name']} (AI Assistant - Mock Engine)",
            "reply": reply, "session_active": False, "handover_triggered": True, "tool_calls": tool_calls,
        }
    elif intent in replies and intent not in ("greeting", "human"):
        reply = replies[intent]
        tool_calls = []
    else:
        reply = replies["greeting"].format(name=user_name)
        tool_calls = []

    return {
        "sender": f"{APARTMENT['name']} (AI Assistant - Mock Engine)",
        "reply": reply,
        "session_active": True,
        "handover_triggered": False,
        "tool_calls": tool_calls,
    }


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", 8010)), reload=True)
