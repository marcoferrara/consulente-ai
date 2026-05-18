import os

# --- MOCK CREDENTIALS ---
# Puoi inserire qui la tua chiave OpenAI o la tua chiave gratuita di Google Gemini!
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCFcMC2HKjmfELzYU2cUT5ZTJAWshPCUdE")
PORT = int(os.getenv("PORT", 8000))

# --- HOTEL INFORMATION ---
HOTEL_NAME = "S'Antiga Charme & Spa"
HOTEL_LOCATION = "Sardegna (Cagliari/Chia)"
DIRECT_BOOKING_BENEFIT = "welcome drink (Vermentino di Gallura e dolcetti sardi) + 1 ora di accesso esclusivo alla SPA"

# --- MOCK PMS DATABASE ---
# Simula le camere disponibili nel database del PMS dell'hotel
ROOMS_DB = [
    {
        "id": "deluxe_mare",
        "name": "Deluxe Vista Mare",
        "price_per_night": 250.0,
        "max_occupancy": 2,
        "available_units": 3
    },
    {
        "id": "junior_suite",
        "name": "Junior Suite con Jacuzzi",
        "price_per_night": 420.0,
        "max_occupancy": 3,
        "available_units": 1
    },
    {
        "id": "classic_giardino",
        "name": "Classic Vista Giardino",
        "price_per_night": 180.0,
        "max_occupancy": 2,
        "available_units": 5
    }
]
