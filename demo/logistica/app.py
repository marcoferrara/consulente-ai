import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, List

app = FastAPI(title="SardiniaLogistics AI API", description="Server di ottimizzazione logistica e rotte montane")

# Abilita CORS per lo sviluppo locale
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Strutture Dati per la simulazione ad alta fedeltà
ROUTES_DATABASE = {
    "rotta_barbagia": {
        "name": "Tratta A — Barbagia Interna",
        "description": "Cagliari -> Nuoro -> Mamoiada -> Orgosolo -> Oliena",
        "standard_time": "3h 45m",
        "optimized_time": "3h 10m",
        "standard_fuel_cost": 82.50,
        "optimized_fuel_cost": 69.30,
        "fuel_saving_percentage": 16.0,
        "co2_saved": "8.4 kg",
        "stops": [
            {"city": "Nuoro", "status": "Consegna completata (Hub)", "delay": "Nessuno"},
            {"city": "Mamoiada", "status": "Ottimizzazione scarico", "delay": "Evitato traffico centro"},
            {"city": "Orgosolo", "status": "Finestra oraria rispettata", "delay": "Nessuno"},
            {"city": "Oliena", "status": "Scarico merci programmato", "delay": "Modificato per mercato"}
        ],
        "weather_alerts": {
            "sole": "Condizioni meteo ideali. Velocità standard consentita sulle statali.",
            "pioggia": "Pioggia battente sulla SS 389. Rallentamento curve Barbagia. AI suggerisce riduzione velocità del 10% e bilanciamento dei pesi a terra.",
            "nebbia": "Fitta nebbia sulla tratta Nuoro-Mamoiada. AI suggerisce deviazione su rotta secondaria SP 22 per visibilità migliore.",
            "neve": "Strada ghiacciata al passo di Caravai. AI impone catene a bordo obbligatorie e anticipo partenza di 45 minuti."
        }
    },
    "rotta_ogliastra": {
        "name": "Tratta B — Ogliastra & Gennargentu",
        "description": "Cagliari -> Lanusei -> Jerzu -> Aritzo -> Tortolì",
        "standard_time": "4h 15m",
        "optimized_time": "3h 30m",
        "standard_fuel_cost": 98.00,
        "optimized_fuel_cost": 81.50,
        "fuel_saving_percentage": 16.8,
        "co2_saved": "10.5 kg",
        "stops": [
            {"city": "Lanusei", "status": "In orario per farmacia territoriale", "delay": "Nessuno"},
            {"city": "Jerzu", "status": "Consegna cantina sociale ottimizzata", "delay": "Anticipato di 20m"},
            {"city": "Aritzo", "status": "Raggiunto prima del blocco pomeridiano", "delay": "Nessuno"},
            {"city": "Tortolì", "status": "Consegna finale al porto", "delay": "Nessuno"}
        ],
        "weather_alerts": {
            "sole": "Cielo sereno sul Gennargentu. Attenzione solo al vento forte di maestrale vicino a Tortolì.",
            "pioggia": "Asfalto viscido sulle pendenze del 12% verso Lanusei. AI suggerisce freno motore automatico attivo.",
            "nebbia": "Visibilità ridotta a 30m sul passo di Aritzo. AI consiglia sosta tecnica o deviazione costiera SS 125.",
            "neve": "Neve pesante al valico del Gennargentu (Aritzo-Tonara). La rotta montana è CHIUSA ai mezzi pesanti. L'AI ricalcola interamente la rotta lungo la costiera Orientale Sarda SS 125 (allungamento di 35km ma 100% sicuro)."
        }
    }
}

FORECAST_DATABASE = {
    "cortes_apertas": {
        "event_name": "Autunno in Barbagia / Cortes Apertas (Mamoiada)",
        "period": "Settembre - Dicembre (Picco weekend)",
        "demand_spike": "+140% Consegne Alimentari e Beverage",
        "desc": "L'apertura dei cortili tradizionali attira oltre 20.000 visitatori a weekend. Le rivendite locali esauriscono le scorte di vino Cannonau e formaggio pecorino entro sabato sera.",
        "predictions": [
            {"item": "Vino Cannonau (Bottiglie)", "current_stock": 250, "recommended_stock": 600, "priority": "CRITICA", "action": "Carico preventivo mercoledì"},
            {"item": "Pecorino Sardo DOP (Forme)", "current_stock": 80, "recommended_stock": 200, "priority": "ALTA", "action": "Rifornimento da caseificio il giovedì"},
            {"item": "Pane Carasau (Confezioni)", "current_stock": 150, "recommended_stock": 450, "priority": "ALTA", "action": "Stoccaggio in hub logistico Nuoro"},
            {"item": "Acqua e Soft Drinks (Casse)", "current_stock": 400, "recommended_stock": 900, "priority": "MEDIA", "action": "Distribuzione ordinaria rinforzata"}
        ],
        "routing_advice": "Il centro di Mamoiada è chiuso al traffico veicolare da venerdì ore 14:00. Le consegne devono essere completate entro le ore 11:30 di venerdì mattina usando l'area di scarico esterna Sud-Ovest."
    },
    "sagra_castagne": {
        "event_name": "Sagra delle Castagne e delle Nocciole (Aritzo)",
        "period": "Fine Ottobre",
        "demand_spike": "+95% Logistica Dolciaria e Packaging",
        "desc": "Grande affluenza di turisti nel borgo montano. Elevata richiesta di sacchetti ecologici, farina di castagne, miele e contenitori per asporto.",
        "predictions": [
            {"item": "Packaging per dolci (Pezzi)", "current_stock": 1000, "recommended_stock": 2500, "priority": "ALTA", "action": "Consegna programmata martedì"},
            {"item": "Farina e Lieviti (Sacchi)", "current_stock": 20, "recommended_stock": 55, "priority": "ALTA", "action": "Rifornimento da Cagliari il mercoledì"},
            {"item": "Miele locale (Vasetti)", "current_stock": 120, "recommended_stock": 250, "priority": "MEDIA", "action": "Prelievo da Jerzu integrato in rotta"},
            {"item": "Contenitori Asporto (Box)", "current_stock": 500, "recommended_stock": 1500, "priority": "CRITICA", "action": "Pre-carico lunedì mattina"}
        ],
        "routing_advice": "Rischio gelate mattutine sulla SP 7 verso Aritzo. Pianificare il transito sul valico non prima delle 10:00. Parcheggio mercato inibito ai bilici, scarico consentito solo a furgoni medio-piccoli."
    },
    "stagione_estiva": {
        "event_name": "Picco Stagione Estiva (Costa Orientale / Tortolì)",
        "period": "Giugno - Agosto",
        "demand_spike": "+180% Logistica HoReCa (Hotel, Ristoranti, Bar)",
        "desc": "La popolazione turistica in Ogliastra quintuplica. Ristoranti e resort costieri a Tortolì, Arbatax e Santa Maria Navarrese richiedono consegne quotidiane di prodotti freschi.",
        "predictions": [
            {"item": "Prodotti Freschi Ortofrutta (kg)", "current_stock": 500, "recommended_stock": 1800, "priority": "CRITICA", "action": "Consegne quotidiane con furgone refrigerato"},
            {"item": "Bevande e Birra Nuraghe (Fusti)", "current_stock": 80, "recommended_stock": 350, "priority": "ALTA", "action": "Carico pesante lunedì e giovedì da Cagliari"},
            {"item": "Prodotti Surgelati (Casse)", "current_stock": 150, "recommended_stock": 400, "priority": "ALTA", "action": "Navetta speciale bisettimanale"},
            {"item": "Tovaglie e Monouso (Box)", "current_stock": 300, "recommended_stock": 700, "priority": "MEDIA", "action": "Consegna cumulativa a inizio settimana"}
        ],
        "routing_advice": "Forte congestione sulla SS 125 Orientale Sarda nelle ore pomeridiane. AI consiglia partenze anticipate alle ore 05:30 da Cagliari per completare le consegne sulla costa entro le 10:30, evitando le ore calde e il traffico balneare."
    }
}

class RouteRequest(BaseModel):
    route_id: str
    weather_condition: str

class ForecastRequest(BaseModel):
    event_id: str

class ChatRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    return {"status": "online", "message": "SardiniaLogistics AI Backend running on port 8086"}

@app.post("/api/route")
def optimize_route(req: RouteRequest):
    route_id = req.route_id.lower()
    weather = req.weather_condition.lower()
    
    if route_id not in ROUTES_DATABASE:
        raise HTTPException(status_code=404, detail="Rotta non trovata")
        
    db_route = ROUTES_DATABASE[route_id]
    
    # Adatta i parametri in tempo reale in base al meteo
    time_str = db_route["optimized_time"]
    fuel_cost = db_route["optimized_fuel_cost"]
    alert = db_route["weather_alerts"].get(weather, "Condizioni ordinarie.")
    saving_pct = db_route["fuel_saving_percentage"]
    
    # Modifiche dinamiche simulate
    if weather == "pioggia":
        time_str = "3h 25m" if route_id == "rotta_barbagia" else "3h 48m"
        fuel_cost += 3.50
        saving_pct -= 1.2
    elif weather == "nebbia":
        time_str = "3h 45m" if route_id == "rotta_barbagia" else "4h 05m"
        fuel_cost += 5.80
        saving_pct -= 2.5
    elif weather == "neve":
        time_str = "4h 10m" if route_id == "rotta_barbagia" else "4h 50m"
        fuel_cost += 12.00
        saving_pct -= 4.8
        
    return {
        "success": True,
        "route_id": route_id,
        "name": db_route["name"],
        "description": db_route["description"],
        "optimized_time": time_str,
        "optimized_fuel_cost": fuel_cost,
        "fuel_saving_percentage": saving_pct,
        "co2_saved": db_route["co2_saved"],
        "stops": db_route["stops"],
        "alert": alert
    }

@app.post("/api/forecast")
def predict_forecast(req: ForecastRequest):
    event_id = req.event_id.lower()
    
    if event_id not in FORECAST_DATABASE:
        raise HTTPException(status_code=404, detail="Evento non trovato")
        
    return {
        "success": True,
        "event_id": event_id,
        "data": FORECAST_DATABASE[event_id]
    }

@app.post("/api/chat")
def logistica_chat(req: ChatRequest):
    query = req.query.lower()
    
    # Logica di risposta basata sulle parole chiave della logistica sarda
    if "meteo" in query or "arizzo" in query or "gennargentu" in query or "neve" in query:
        reply = (
            "<b>Pianificatore AI:</b> Con neve o nebbia sul Gennargentu (tratta SP 7 / Aritzo), le pendenze elevate del 12% "
            "e il ghiaccio rendono pericoloso il transito dei mezzi oltre le 3.5 tonnellate. L'AI consiglia la deviazione costiera "
            "sulla SS 125 Orientale Sarda. Sebbene allunghi il tragitto di 35 km, riduce il tempo di percorrenza effettivo di "
            "40 minuti (evitando blocchi stradali) e azzera il rischio di incidenti o fermi del mezzo. Ricordarsi le catene a bordo."
        )
    elif "mamoiada" in query or "cortes" in query or "scarico" in query or "festa" in query:
        reply = (
            "<b>Pianificatore AI:</b> Durante gli eventi ad alta affluenza come *Cortes Apertas* a Mamoiada, il centro storico "
            "è completamente transennato da venerdì alle 14:00. Il nostro algoritmo ha ricalcolato gli orari di consegna: "
            "consigliamo un anticipo del carico a mercoledì notte e scarico tassativo venerdì entro le ore 11:30 nell'Hub provvisorio "
            "di via Nuoro (fronte campo sportivo). Questo evita blocchi del furgone e garantisce il rifornimento in tempo delle cantine sociali."
        )
    elif "carburante" in query or "risparmio" in query or "costo" in query:
        reply = (
            "<b>Pianificatore AI:</b> Attivando il modulo di ottimizzazione predittiva delle rotte (che combina storico ordini, "
            "previsioni meteo stradali e accorpamento dei carichi HoReCa), la flotta ha registrato nelle ultime 4 settimane: "
            "<br>- Risparmio medio di carburante pari al <b>15.8%</b>."
            "<br>- Riduzione dei chilometri a vuoto del <b>22%</b>."
            "<br>- Taglio di emissioni CO₂ pari a circa <b>95kg</b> a settimana per motrice."
            "<br>- Azzeramento totale dei ritardi e delle mancate consegne dovute a Out-of-Stock."
        )
    elif "carico" in query or "camion" in query or "bilanciamento" in query:
        reply = (
            "<b>Pianificatore AI:</b> Le strade interne della Sardegna centrale (Barbagia/Ogliastra) presentano pendenze ripide "
            "e curve a raggio ridotto. Per evitare lo sbilanciamento del baricentro (rischio ribaltamento), il sistema predittivo "
            "suggerisce di posizionare sempre i carichi pesanti (fusti di birra, casse di vino, formaggi DOP) sulla piattaforma inferiore del camion, "
            "lasciando i beni leggeri (packaging, tovaglie) in alto. Attualmente il camion della tratta A ha un bilanciamento ottimale dell'<b>88%</b>."
        )
    else:
        reply = (
            "<b>Pianificatore AI:</b> Ricevuto. La richiesta è stata analizzata dal nostro motore predittivo. Sulla base dello storico "
            "delle consegne della flotta PMI Sardegna e delle finestre orarie del traffico montano, suggeriamo di ottimizzare la rotta selezionata "
            "attraverso il pulsante 'Calcola Rotta Ottimizzata' per vedere l'impatto reale su consumi e tempi."
        )
        
    return {
        "success": True,
        "reply": reply
    }

# Servire i file statici (se presenti nella stessa directory)
# In produzione o test locale, app.py servirà direttamente index.html
try:
    app.mount("/", StaticFiles(directory=".", html=True), name="static")
except Exception:
    pass

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8086, reload=True)
