import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PORT = int(os.getenv("PORT", 8002))

WINERY_NAME = "Tenute Ichnos"
WINERY_LOCATION = "Jerzu, Ogliastra – Sardegna"
WINERY_FOUNDED = 1932
WINERY_HECTARES = 45
WINERY_ANNUAL_BOTTLES = 120000
WINERY_BIO = "Produttori di vini autoctoni sardi da quattro generazioni nel cuore dell'Ogliastra, una delle cinque Blue Zone mondiali."
