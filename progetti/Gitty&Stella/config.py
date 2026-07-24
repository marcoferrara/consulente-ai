import os

# --- MOCK CREDENTIALS ---
# Inserisci qui la tua chiave OpenAI oppure una chiave gratuita di Google Gemini.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here")
PORT = int(os.getenv("PORT", 8010))

# --- DATI APPARTAMENTO ---
# PLACEHOLDER: dati di esempio plausibili, da verificare/confermare con il proprietario.
APARTMENT = {
    "name": "Gitty&Stella",
    "slug": "gitty-stella",
    "address": "Via Sardegna, Oristano (OR), Sardegna, Italia",
    "lat": 39.9033,
    "lng": 8.5897,
    "size_sqm": 65,
    "bedrooms": 2,
    "bathrooms": 1,
    "max_occupancy": 4,
    "base_price_per_night": 85.0,
    "cleaning_fee": 25.0,
    "long_stay_discount_threshold_nights": 7,
    "long_stay_discount_percent": 15,
    "amenities": [
        "wifi", "aria_condizionata", "cucina_completa", "lavatrice",
        "parcheggio_gratuito", "check_in_autonomo", "tv", "culla_su_richiesta"
    ],
    "image_urls": [
        "/static/images/soggiorno_1.jpg",
        "/static/images/camera_1.jpg",
        "/static/images/cucina_1.jpg",
        "/static/images/bagno_1.jpg",
    ],
}

# Intervalli mock già occupati, per rendere credibile la demo di disponibilità.
# PLACEHOLDER: dati fittizi, da sostituire con un calendario reale (es. Google Calendar) in una fase futura.
MOCK_BOOKED_RANGES = [
    {"checkin": "2026-08-10", "checkout": "2026-08-17"},
    {"checkin": "2026-09-01", "checkout": "2026-09-05"},
]

DIRECT_BOOKING_BENEFIT = "nessuna commissione di intermediazione, prezzo netto e risposta rapida via WhatsApp"

# --- DATI PROPRIETARIO (per la notifica mock) ---
# PLACEHOLDER: da sostituire con i contatti reali del proprietario.
OWNER_INFO = {
    "name": "Proprietario Gitty&Stella",
    "notification_channel": "whatsapp_owner_mock",
    "contact_phone": "+39 000 0000000",
    "contact_email": "proprietario@example.com",
}
