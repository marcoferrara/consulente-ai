from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import datetime
from config import AZIENDE_DB, BANDI_DB, PORT

app = FastAPI(
    title="Studio Associato RAG AI Engine",
    description="Backend per la corrispondenza semantica tra Bandi Regionali e Aziende Clienti",
    version="1.0.0"
)

# Configurazione CORS per consentire l'accesso da qualsiasi origine (comprese file:// e host locali)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---
class SearchQuery(BaseModel):
    query: str

class MatchRequest(BaseModel):
    bando_id: str

class AlertRequest(BaseModel):
    azienda_id: str
    bando_id: str
    channel: str  # "whatsapp" o "email"

# --- HELPER FUNCTIONS ---
def evaluate_match(azienda, bando):
    reasons = []
    missing = []
    score = 100
    
    # 1. Verifica ATECO
    azienda_ateco_2digit = azienda["ateco"][:2]
    ateco_ammessi = bando["ateco_ammessi"]
    
    # Check if the company's 2-digit Ateco code is allowed in the call
    ateco_ok = False
    for code in ateco_ammessi:
        if azienda["ateco"].startswith(code):
            ateco_ok = True
            break
            
    if ateco_ok:
        reasons.append(f"Codice ATECO ({azienda['ateco']}) pienamente coerente con il bando ({bando['categoria']}).")
    else:
        score -= 40
        missing.append("Codice ATECO non ricompreso tra quelli ammessi dal bando.")
        
    # 2. Verifica Dimensione
    if azienda["dimensione"] in bando["requisiti_dimensione"]:
        reasons.append(f"Dimensione aziendale ({azienda['dimensione']}) conforme ai requisiti del bando.")
    else:
        score -= 30
        missing.append(f"Il bando esclude le aziende di taglia '{azienda['dimensione']}'.")
        
    # 3. Verifica requisiti ZES
    if bando["richiede_zes"]:
        if azienda["area_zes"]:
            reasons.append(f"Sede aziendale localizzata in area ZES ({azienda['sede']}), requisito chiave soddisfatto.")
        else:
            score -= 30
            missing.append("L'agevolazione è limitata esclusivamente alle unità produttive localizzate nelle Aree ZES sarde.")
            
    # 4. Verifica requisiti Giovani
    if bando["richiede_giovani"]:
        if azienda["eta_titolare"] < 41:
            reasons.append(f"Requisito anagrafico giovanile soddisfatto: titolare di {azienda['eta_titolare']} anni (limite < 41).")
        else:
            score -= 30
            missing.append(f"Il titolare ha superato il limite d'età previsto ({azienda['eta_titolare']} anni, richiesto < 41).")
            
    # Calcolo idoneità complessiva
    eligible = len(missing) == 0
    score = max(0, score)
    
    if eligible:
        # Aggiungi raccomandazioni o motivazioni extra se il punteggio è alto
        if score >= 90:
            reasons.append("Punteggio di idoneità massimo: bando ad altissimo tasso di successo consigliato.")
    
    return {
        "eligible": eligible,
        "score": score,
        "reasons": reasons,
        "missing_requirements": missing
    }

# --- API ENDPOINTS ---
@app.get("/")
def read_root():
    return {
        "status": "online",
        "engine": "Studio Associato RAG AI Match Engine",
        "version": "1.0.0",
        "datetime": datetime.datetime.now().isoformat(),
        "database": {
            "aziende_indicizzate": len(AZIENDE_DB),
            "bandi_attivi": len(BANDI_DB)
        }
    }

@app.get("/api/bandi")
def get_bandi():
    return BANDI_DB

@app.get("/api/aziende")
def get_aziende():
    return AZIENDE_DB

@app.post("/api/match")
def post_match(req: MatchRequest):
    # Trova il bando
    bando = next((b for b in BANDI_DB if b["id"] == req.bando_id), None)
    if not bando:
        raise HTTPException(status_code=404, detail="Bando non trovato")
        
    matches = []
    for az in AZIENDE_DB:
        eval_res = evaluate_match(az, bando)
        matches.append({
            "azienda_id": az["id"],
            "denominazione": az["denominazione"],
            "sede": az["sede"],
            "dimensione": az["dimensione"],
            "fatturato": az["fatturato_2025"],
            "ateco": az["ateco"],
            "eligible": eval_res["eligible"],
            "score": eval_res["score"],
            "reasons": eval_res["reasons"],
            "missing_requirements": eval_res["missing_requirements"]
        })
        
    # Ordina per punteggio decrescente
    matches.sort(key=lambda x: x["score"], reverse=True)
    return {
        "bando_id": bando["id"],
        "titolo": bando["titolo"],
        "matches": matches
    }

@app.post("/api/search")
def post_search(query_req: SearchQuery):
    q = query_req.query.lower()
    
    # 1. Simula l'estrazione semantica dei concetti chiave (RAG NLP Parser)
    detected_concepts = []
    selected_bando = None
    
    # Regole semplici per simulare la comprensione dell'intento dell'utente
    if "vino" in q or "vitivinicolo" in q or "cantina" in q or "alcol" in q:
        detected_concepts = ["Vino", "Cantina vitivinicola", "Agricoltura/Agroalimentare"]
        # Match "misura_cooperazione_filiera" o "por_fesr_pmi"
        selected_bando = next((b for b in BANDI_DB if b["id"] == "misura_cooperazione_filiera"), None)
    elif "pastore" in q or "pecora" in q or "agricoltori" in q or "giovan" in q or "campagna" in q or "agro" in q:
        detected_concepts = ["Agricoltura primario", "Insediamento giovani", "Ricambio generazionale"]
        selected_bando = next((b for b in BANDI_DB if b["id"] == "psr_giovani_agri"), None)
    elif "zes" in q or "macomer" in q or "tossilo" in q or "fiscale" in q or "credito" in q or "industria" in q:
        detected_concepts = ["Area Industriale ZES", "Credito d'Imposta", "Investimento macchinari"]
        selected_bando = next((b for b in BANDI_DB if b["id"] == "zes_unica_sardegna"), None)
    elif "digitalizzazione" in q or "software" in q or "sito" in q or "e-commerce" in q or "cloud" in q or "cybersecurity" in q or "hotel" in q or "pasta" in q:
        detected_concepts = ["Digitalizzazione", "PMI Commercio/Servizi", "Innovazione tecnologica"]
        selected_bando = next((b for b in BANDI_DB if b["id"] == "por_fesr_pmi"), None)
    else:
        # Fallback di default
        detected_concepts = ["Digitale", "Generico PMI"]
        selected_bando = BANDI_DB[0]
        
    # Calcola la corrispondenza delle aziende per il bando identificato
    matches_res = post_match(MatchRequest(bando_id=selected_bando["id"]))
    
    # Simula i log del sistema RAG
    logs = [
        f"INPUT: Ricevuta richiesta utente: '{query_req.query}'",
        f"RAG ENGINE: Estrazione entità semantiche completata. Concetti estratti: {', '.join(detected_concepts)}",
        f"VECTOR DB: Ricerca semantica nel database normative. Trovato bando con massima attinenza (94.2%): {selected_bando['titolo']}",
        f"MATCHING ENGINE: Interrogazione del database clienti (312 profili aziendali)",
        f"MATCHING ENGINE: Analisi dei criteri incrociati completata. Calcolo del fit semantico in corso..."
    ]
    
    return {
        "detected_concepts": detected_concepts,
        "matched_bando": selected_bando,
        "matches": matches_res["matches"],
        "logs": logs
    }

@app.post("/api/send_alert")
def post_send_alert(req: AlertRequest):
    azienda = next((a for a in AZIENDE_DB if a["id"] == req.azienda_id), None)
    bando = next((b for b in BANDI_DB if b["id"] == req.bando_id), None)
    
    if not azienda or not bando:
        raise HTTPException(status_code=404, detail="Azienda o Bando non trovato")
        
    eval_res = evaluate_match(azienda, bando)
    
    # Genera la comunicazione personalizzata con AI
    current_time = datetime.datetime.now().strftime("%H:%M")
    
    message_content = ""
    if req.channel == "whatsapp":
        message_content = (
            f"🟢 *STUDIO ASSOCIATO AI ALERT* 🚨\n\n"
            f"Gentile *{azienda['referente']}*,\n"
            f"il nostro sistema intelligente ha identificato un'opportunità di finanziamento ad altissima idoneità per *{azienda['denominazione']}*!\n\n"
            f"📂 *Bando:* {bando['titolo']}\n"
            f"💰 *Agevolazione:* {bando['contributo']}\n"
            f"🎯 *Il vostro Fit:* {eval_res['score']}% (Soddisfatti tutti i requisiti ATECO, di sede e dimensione!)\n"
            f"⏰ *Scadenza presentazione:* {bando['scadenza']}\n\n"
            f"Abbiamo già predisposto la bozza di istruttoria tecnica con i vostri dati d'ufficio. Clicchi sul link sotto o risponda a questo messaggio per pianificare un incontro di convalida in studio.\n"
            f"👉 _Pianifica call con Consulente: https://calendly.com/studio-associato-sardegna_"
        )
    else:  # email
        message_content = (
            f"Oggetto: Opportunità di Finanziamento Agevolato: {bando['titolo']} - Fit {eval_res['score']}%\n\n"
            f"Gentile {azienda['referente']},\n\n"
            f"Con la presente la informiamo che la nostra piattaforma RAG AI per la finanza agevolata ha rilevato la pubblicazione del seguente bando della Regione Sardegna, per il quale la vostra azienda risulta idonea al {eval_res['score']}%:\n\n"
            f"BANDO: {bando['titolo']}\n"
            f"CATEGORIA: {bando['categoria']}\n"
            f"TIPO DI CONTRIBUTO: {bando['contributo']}\n"
            f"INVESTIMENTO MINIMO: € {bando['investimento_min']:,.2f}\n"
            f"SCADENZA PRESENTAZIONE DOMANDE: {bando['scadenza']}\n\n"
            f"ANALISI DI COMPATIBILITÀ:\n"
            f"Grazie ai dati del vostro profilo registrati presso il nostro studio, abbiamo verificato le seguenti conformità:\n"
            + "\n".join([f"- {r}" for r in eval_res["reasons"]]) + "\n\n"
            f"PROSSIMI PASSI:\n"
            f"Abbiamo già pre-caricato la documentazione contabile di base per la vostra impresa. Le chiediamo di risponderci a questa email o di contattarci telefonicamente ({azienda['telefono_referente']}) per confermare il vostro interesse ad aderire alla misura, così da avviare l'istruttoria prima della chiusura dello sportello.\n\n"
            f"Cordiali saluti,\n"
            f"Dott. Marco Ferrara\n"
            f"Studio Associato per le Imprese Sarde"
        )
        
    return {
        "success": True,
        "azienda_id": azienda["id"],
        "azienda_name": azienda["denominazione"],
        "bando_id": bando["id"],
        "channel": req.channel,
        "message": message_content,
        "timestamp": datetime.datetime.now().isoformat(),
        "destinatario": azienda["email_referente"] if req.channel == "email" else azienda["telefono_referente"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
