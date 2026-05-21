import os
import json
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="SardiniaCraft AI Server",
    description="Server di backend per il copilota AI dell'Artigianato Sardo d'Eccellenza.",
    version="1.0.0"
)

# Configura CORS per permettere test agili
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database interno dei prodotti tradizionali (preset)
PRODUCT_DATABASE = {
    "fede_sarda": {
        "id": "fede_sarda",
        "symbols": "Filigrana d'oro, nido d'ape, sferette/granuli",
        "meaning": "La leggenda narra che le Janas (le fate sarde) tessessero fili d'oro. Il nido d'ape rappresenta prosperità, fedeltà e famiglia. I granuli simboleggiano chicchi di grano per abbondanza e ricchezza.",
        "titles": {
            "it": "Fede Sarda Classica in Filigrana d'Oro Giallo",
            "en": "Classic Golden Filigree Sardinian Wedding Ring",
            "de": "Klassischer sardischer Ehering aus Goldfiligran"
        },
        "descriptions": {
            "it": "Questa splendida Fede Sarda è interamente realizzata a mano in oro giallo 18 carati nel nostro laboratorio, utilizzando la tradizionale tecnica della filigrana. Ogni singolo cerchio e microscopico granulo viene posizionato manualmente con pazienza infinita, riproducendo il classico disegno a nido d'ape. Simbolo di amore eterno, protezione e prosperità, è un pezzo unico intriso di storia e cultura sarda.",
            "en": "This exquisite Sardinian Wedding Ring is entirely handcrafted in 18k yellow gold in our workshop, using the traditional filigree technique. Every single loop and micro-granule is placed by hand with infinite patience, reproducing the classic honeycomb pattern. A symbol of eternal love, protection, and prosperity, it is a unique piece rich in Sardinian history and culture.",
            "de": "Dieser exquisite sardische Ehering ist komplett in Handarbeit aus 18-karätigem Gelbgold in unserer Werkstatt unter Verwendung der traditionellen Filigran-Technik gefertigt. Jede einzelne Schleife und jedes Mikrogranulat wird mit unendlicher Geduld von Hand platziert und reproduziert das klassische Wabenmuster. Als Symbol für ewige Liebe, Schutz und Wohlstand ist es ein einzigartiges Stück reich an sardischer Geschichte und Kultur."
        },
        "specs": {
            "it": "Materiale: Oro Giallo 18k. Lavorazione: Filigrana fatta a mano. Larghezza fascia: 8mm. Peso: 4.8g.",
            "en": "Material: 18k Yellow Gold. Craft: Handmade Filigree. Band Width: 8mm. Weight: 4.8g.",
            "de": "Material: 18k Gelbgold. Handwerk: Handgefertigtes Filigran. Bandbreite: 8mm. Gewicht: 4.8g."
        },
        "tags": "fede sarda, filigrana, oro giallo, fatto a mano, gioielli sardi, sardinian jewelry, unique pieces",
        "price": 380.00,
        "weight": 0.05
    },
    "tappeto_mogoro": {
        "id": "tappeto_mogoro",
        "symbols": "Pavoncella sarda, fiori selvatici, greche geometriche",
        "meaning": "La pavoncella sarda è il simbolo più iconico dell'artigianato dell'isola: rappresenta la rigenerazione, la fertilità, l'abbondanza e il ritorno della primavera. Le greche geometriche esterne proteggono il focolare domestico.",
        "titles": {
            "it": "Tappeto Sardo di Mogoro con Pavoncelle",
            "en": "Handwoven Mogoro Sardinian Carpet with Peafowl Motif",
            "de": "Handgewebter sardischer Mogoro-Teppich mit Pfauenmotiv"
        },
        "descriptions": {
            "it": "Tessuto interamente a mano su telaio verticale tradizionale a Mogoro, questo splendido tappeto in pura lana sarda combina design contemporaneo e simbolismo ancestrale. Il motivo centrale ospita la pavoncella sarda, emblema di rinascita e prosperità, tessuta con un contrasto cromatico profondo. Le frange e le finiture sono rifinite rigorosamente a mano.",
            "en": "Entirely handwoven on a traditional vertical loom in Mogoro, this gorgeous pure Sardinian wool carpet combines contemporary design and ancestral symbolism. The central motif features the Sardinian peafowl, emblem of rebirth and prosperity, woven in deep contrast colors. The fringes and borders are strictly hand-finished.",
            "de": "Komplett handgewebt auf einem traditionellen vertikalen Webstuhl in Mogoro, kombiniert dieser wunderschöne Teppich aus reiner sardischer Wolle zeitgenössisches design mit überlieferter Symbolik. Das zentrale Motiv zeigt den sardischen Pfau, ein Emblem der Wiedergeburt und des Wohlstands, gewoben in tiefen Kontrastfarben. Die Fransen und Kanten sind komplett handgefertigt."
        },
        "specs": {
            "it": "Materiale: 100% Lana Sarda. Telaio: Verticale manuale. Dimensioni: 120 x 180 cm. Lavaggio: A secco.",
            "en": "Material: 100% Sardinian Wool. Loom: Hand vertical. Dimensions: 120 x 180 cm. Care: Dry clean.",
            "de": "Material: 100% sardische Wolle. Webstuhl: Manueller vertikaler Webstuhl. Maße: 120 x 180 cm. Pflege: Chemische Reinigung."
        },
        "tags": "tappeto sardo, lana sarda, mogoro, fatto a mano, pavoncella sarda, sardinian carpet, home decor",
        "price": 850.00,
        "weight": 4.5
    },
    "brocca_sposa": {
        "id": "brocca_sposa",
        "symbols": "Decorazioni floreali a rilievo, uccellini d'amore",
        "meaning": "La Brocca della Sposa è un capolavoro della ceramica sarda. Utilizzata storicamente per portare l'acqua durante il corteo nuziale, è decorata con rilievi floreali e due uccellini sul becco, simboli di fedeltà coniugale, amore e nuova vita insieme.",
        "titles": {
            "it": "Brocca della Sposa Tradizionale in Ceramica Smaltata",
            "en": "Traditional Sardinian Bride Jug in Glazed Ceramic",
            "de": "Traditionelle sardische Brautkanne aus glasierter Keramik"
        },
        "descriptions": {
            "it": "Questa brocca cerimoniale è plasmata al tornio e decorata interamente a mano in argilla cotta e smaltata con finitura bianco lucida. I decori a rilievo riproducono fiori della macchia mediterranea e due uccellini che si incontrano sul becco, celebrando l'unione e la fedeltà. Un elemento decorativo d'eccezione, perfetto connubio di utilità storica e poesia visiva.",
            "en": "This ceremonial jug is thrown on the wheel and entirely hand-decorated in fired clay, then finished with a glossy white glaze. The relief patterns reproduce Mediterranean flowers and two birds meeting on the spout, celebrating union and fidelity. An exceptional decorative element, a perfect blend of historic utility and visual poetry.",
            "de": "Diese zeremonielle Kanne wird auf der Töpferscheibe gedreht und komplett von Hand aus gebranntem Ton dekoriert und mit einer glänzend weißen Glasur veredelt. Die Reliefmuster stellen mediterrane Blumen und zwei Vögel dar, die sich auf dem Ausguss treffen und Vereinigung und Treue feiern. Ein außergewöhnliches dekoratives Element, eine perfekte Mischung aus historischem Nutzen und visueller Poesie."
        },
        "specs": {
            "it": "Materiale: Argilla locale smaltata. Lavorazione: Fatta al tornio e decorata a mano. Altezza: 32cm. Peso: 1.8kg.",
            "en": "Material: Glazed local clay. Craft: Wheel-thrown & hand-decorated. Height: 32cm. Weight: 1.8kg.",
            "de": "Material: Glasierter lokaler Ton. Handwerk: Auf der Töpferscheibe gedreht & handdekoriert. Höhe: 32cm. Gewicht: 1.8kg."
        },
        "tags": "ceramica sarda, brocca della sposa, fatto a mano, ceramica artistica, sardinian ceramic, wedding gift",
        "price": 190.00,
        "weight": 2.0
    }
}

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="File index.html non trovato.")
    
    with open(index_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return html_content

@app.post("/api/analyze")
async def analyze_product(request: Request):
    try:
        data = await request.json()
        product_id = data.get("product_id")
        
        if not product_id or product_id not in PRODUCT_DATABASE:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "ID Prodotto non valido o non fornito."}
            )
            
        product = PRODUCT_DATABASE[product_id]
        
        return {
            "success": True,
            "data": product,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Errore interno di analisi Vision AI: {str(e)}"}
        )

@app.post("/api/shipping")
async def calculate_shipping(request: Request):
    try:
        data = await request.json()
        query = data.get("query", "").lower()
        product_id = data.get("product_id", "fede_sarda")
        
        product = PRODUCT_DATABASE.get(product_id, PRODUCT_DATABASE["fede_sarda"])
        weight = product["weight"]
        value = product["price"]
        
        # Logica di calcolo dinamico basata sul testo della domanda
        destination = "unspecified"
        if any(x in query for x in ["usa", "america", "stati uniti", "new york", "ny", "states"]):
            destination = "USA"
            cost = 35.00 if weight < 1.0 else (35.00 + (weight - 1.0) * 8.00)
            transit_days = "3-5 giorni lavorativi"
            courier = "DHL Express International"
            # USA ha dazi esenti per arte/artigianato o sotto gli $800
            duties = "Esente da dazi doganali (sotto la soglia minima di 800 USD - US De Minimis)."
            if value > 800:
                duties = "Calcolato circa 3.2% di dazio all'importazione."
                
            reply_text = f"Yes, we absolutely ship to the USA! For the '{product['titles']['en']}', the shipping cost via {courier} is ${cost:.2f} with fully tracked courier service. The estimated delivery time is {transit_days}. Regarding customs duties, {duties} All our shipments are securely packed in custom padded wood casings to protect the fine craftsmanship during transit."
            
        elif any(x in query for x in ["germania", "germany", "deutschland", "berlin", "monaco"]):
            destination = "Germania"
            cost = 15.00 if weight < 1.0 else (15.00 + (weight - 1.0) * 3.00)
            transit_days = "2-3 giorni lavorativi"
            courier = "UPS Standard Europe"
            duties = "Esente (Mercato Comune Europeo / Nessuna barriera doganale)."
            
            reply_text = f"Ja, wir versenden sehr gerne nach Deutschland! Für '{product['titles']['de']}' betragen die Versandkosten mit {courier} nur €{cost:.2f} (inklusive vollständiger Online-Sendungsverfolgung). Die voraussichtliche Lieferzeit beträgt {transit_days}. Da wir uns im europäischen Binnenmarkt befinden, fallen keinerlei Zollgebühren oder zusätzliche Steuern an. Das Produkt wird in einer edlen, gepolsterten Schutzbox verpackt."
            
        elif any(x in query for x in ["giappone", "japan", "tokyo"]):
            destination = "Giappone"
            cost = 45.00 if weight < 1.0 else (45.00 + (weight - 1.0) * 12.00)
            transit_days = "5-7 giorni lavorativi"
            courier = "FedEx Priority International"
            duties = "Soggetto ad IVA locale all'importazione (circa 10% sdoganamento gratuito)."
            
            reply_text = f"Yes, we provide fully insured shipping to Japan. For the '{product['titles']['en']}', the shipping fee is ${cost:.2f} using {courier}. Transit time is approximately {transit_days}. Customs duties in Japan are calculated based on the local import tax (around 10%), handled directly by the courier for a smooth delivery. The item is packed inside an elegant velvet pouch and a robust wooden gift box."
            
        elif any(x in query for x in ["assicura", "insur", "damage", "dannegg"]):
            # Domanda generica su assicurazione
            cost = 15.00
            reply_text = "Tutte le nostre spedizioni internazionali sono protette da una copertura assicurativa totale al 100% contro furto, smarrimento o danneggiamento durante il transito. Nel rarissimo caso in cui un manufatto unico subisca danni, provvederemo immediatamente al rimborso totale o alla ri-creazione prioritaria del pezzo d'intesa con te. Utilizziamo imballi rigidi a triplo strato per la massima sicurezza."
        else:
            # Fallback generico
            destination = "Europa"
            cost = 20.00
            transit_days = "3-4 giorni lavorativi"
            courier = "DHL Standard"
            duties = "Verificare in base al Paese."
            reply_text = f"Grazie per la richiesta! Spediamo in tutto il mondo con corriere espresso tracciato. Per questo articolo, il costo base di spedizione è di circa €{cost:.2f} con consegna stimata in {transit_days}. Ogni pezzo viene imballato a mano in confezione regalo rigida ed eco-sostenibile per preservare il valore unico dell'opera."
            
        return {
            "success": True,
            "query": query,
            "product_id": product_id,
            "destination": destination,
            "shipping_cost": cost,
            "transit_time": transit_days,
            "courier": courier,
            "duties": duties,
            "reply": reply_text,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Errore nell'assistente spedizioni: {str(e)}"}
        )

if __name__ == "__main__":
    print("SardiniaCraft AI Server attivo su http://127.0.0.1:8085")
    uvicorn.run("app:app", host="127.0.0.1", port=8085, reload=True)
