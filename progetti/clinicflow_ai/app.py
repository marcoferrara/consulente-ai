import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, List
import random
from datetime import datetime

app = FastAPI(
    title="ClinicFlow AI API",
    description="Sistema di Triage Virtuale e Assistente Preparazione Esami per Poliambulatori"
)

# Abilita CORS per lo sviluppo locale
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database in-memory dei dettagli di preparazione esami
EXAMS_DATABASE = {
    "ecografia_addome": {
        "name": "Ecografia Addome Completo",
        "category": "Ecografia",
        "description": "Esame ecografico degli organi addominali (fegato, colecisti, vie biliari, pancreas, milza, reni, aorta, vescica, utero/ovaie o prostata).",
        "instructions": [
            "**Digiuno**: Tassativo digiuno da cibi solidi nelle 6 ore precedenti l'esame.",
            "**Liquidi**: Nelle 2 ore precedenti l'esame, bere 1 litro di acqua naturale non gassata.",
            "**Urinare**: Non urinare nelle 2 ore precedenti l'esame. La vescica deve essere ben piena per visualizzare correttamente gli organi pelvici.",
            "**Dieta nei giorni precedenti**: Nei 2 giorni precedenti l'esame, evitare cibi che producono aria nell'intestino (verdure a foglia larga, legumi, bibite gassate, frutta, pane, pasta)."
        ]
    },
    "risonanza_contrasto": {
        "name": "Risonanza Magnetica con Contrasto",
        "category": "Risonanza Magnetica",
        "description": "Indagine diagnostica ad alta risoluzione che utilizza un campo magnetico e un mezzo di contrasto endovenoso.",
        "instructions": [
            "**Digiuno**: Digiuno assoluto da solidi e liquidi da almeno 6 ore.",
            "**Esami preliminari**: È obbligatorio portare con sei l'esame della Creatininemia recente (non più vecchio di 30 giorni) per valutare la funzionalità renale.",
            "**Oggetti metallici**: Rimuovere qualsiasi oggetto metallico prima di entrare nella sala (orologi, gioielli, chiavi, forcine, carte di credito, protesi acustiche).",
            "**Pacemaker / Dispositivi**: Segnalare immediatamente l'eventuale presenza di pacemaker cardiaco, clip vascolari cerebrali, schegge metalliche o protesi metalliche."
        ]
    },
    "esami_sangue": {
        "name": "Esami del Sangue Ordinari",
        "category": "Laboratorio Analisi",
        "description": "Prelievo ematico standard per la misurazione dei principali parametri biochimici ed ematologici.",
        "instructions": [
            "**Digiuno**: Digiuno di almeno 8-12 ore (cena leggera la sera precedente). Evitare assolutamente alcolici e caffeina nelle 12 ore precedenti.",
            "**Acqua**: È consentito bere modiche quantità di acqua naturale non gassata al mattino.",
            "**Farmaci**: Salvo diversa indicazione del medico curante, assumere i farmaci abituali (es. per la pressione) solo dopo il prelievo.",
            "**Riposo**: Evitare sforzi fisici intensi nelle 12 ore precedenti il prelievo."
        ]
    },
    "holter_cardiaco": {
        "name": "Elettrocardiogramma Dinamico secondo Holter",
        "category": "Cardiologia",
        "description": "Registrazione continua dell'attività elettrica del cuore per 24 o 48 ore mediante un dispositivo portatile.",
        "instructions": [
            "**Igiene personale**: Fare una doccia accurata subito prima dell'applicazione del dispositivo, poiché non sarà possibile bagnare l'apparecchio durante tutto il periodo di registrazione.",
            "**Abbigliamento**: Indossare abiti comodi, preferibilmente camicie o magliette abbottonate davanti per facilitare il passaggio dei cavi degli elettrodi.",
            "**Attività ordinaria**: Durante il test, condurre la propria vita abituale senza limitazioni, evitando però l'uso di termoperle o coperte elettriche.",
            "**Diario del paziente**: Annotare sul foglio consegnato gli orari di eventuali sintomi avvertiti (palpitazioni, capogiri, dolore) e l'attività svolta."
        ]
    },
    "gastroscopia": {
        "name": "Gastroscopia (EGDS)",
        "category": "Endoscopia",
        "description": "Esame endoscopico che consente la visione diretta dell'esofago, dello stomaco e del duodeno.",
        "instructions": [
            "**Digiuno**: Tassativo digiuno da cibi solidi e liquidi da almeno 8 ore precedenti l'esame.",
            "**Farmaci antiacidi**: Sospendere l'assunzione di gastroprotettori e antiacidi (es. omeprazolo, pantoprazolo) da almeno 5-7 giorni prima, se prescritto per la ricerca dell'Helicobacter Pylori.",
            "**Terapia anticoagulante**: Se si assumono farmaci anticoagulanti (es. Cardioaspirina, Coumadin), contattare il medico curante almeno 7 giorni prima per l'eventuale sospensione o sostituzione temporanea.",
            "**Accompagnatore**: Trattandosi di un esame spesso eseguito in sedazione, è obbligatorio venire accompagnati da una persona adulta e non guidare per le 12 ore successive."
        ]
    }
}

# Coda simulata dei pazienti in attesa di triage gestita dall'operatore
TRIAGE_QUEUE = [
    {
        "id": "pat_1",
        "name": "Giuseppe Rossi",
        "age": 62,
        "symptoms": "Forte dolore toracico opprimente che si irradia al braccio sinistro, difficoltà a respirare da circa 20 minuti.",
        "specialty": "Cardiologia",
        "urgency": "ROSSO",
        "time": "11:32"
    },
    {
        "id": "pat_2",
        "name": "Maria Bianchi",
        "age": 45,
        "symptoms": "Dolore acuto al ginocchio destro dopo una caduta accidentale. Forte gonfiore e impossibilità di appoggiare il piede.",
        "specialty": "Ortopedia",
        "urgency": "GIALLO",
        "time": "11:15"
    },
    {
        "id": "pat_3",
        "name": "Luca Neri",
        "age": 28,
        "symptoms": "Prurito intenso e comparsa di macchie rosse in rilievo sul tronco e sulle braccia dopo assunzione di un farmaco.",
        "specialty": "Dermatologia",
        "urgency": "GIALLO",
        "time": "10:54"
    },
    {
        "id": "pat_4",
        "name": "Francesca Verdi",
        "age": 37,
        "symptoms": "Bruciore persistente allo stomaco da alcune settimane, accentuato dopo i pasti. Nausea occasionale.",
        "specialty": "Gastroenterologia",
        "urgency": "VERDE",
        "time": "10:12"
    }
]

# Modelli di richiesta Pydantic
class TriageRequest(BaseModel):
    patient_name: str
    patient_age: int
    symptoms: str

class ExamRequest(BaseModel):
    exam_id: str

class ChatQueryRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "ClinicFlow AI Backend running on port 8087"
    }

@app.post("/api/triage")
def perform_triage(req: TriageRequest):
    symptoms_lower = req.symptoms.lower()
    
    # Valori di default
    specialty = "Medicina Generale"
    urgency = "VERDE"
    advice = "Consigliamo di programmare una visita con il proprio medico di base per approfondire la situazione."
    
    # 1. Regole per Cardiologia (Urgente/Critico)
    if any(k in symptoms_lower for k in ["petto", "toracico", "affanno", "palpitazioni", "cardiaco", "aritmia", "braccio sinistro", "dispnea"]):
        specialty = "Cardiologia"
        if any(k in symptoms_lower for k in ["forte dolore", "opprimente", "mancanza fiato", "fiato corto", "svenimento", "collasso"]):
            urgency = "ROSSO"
            advice = "ATTENZIONE: I sintomi descritti potrebbero indicare una situazione di emergenza cardiaca. SI CONSIGLIA DI CHIAMARE IMMEDIATAMENTE IL 112 O RECARSI AL PRONTO SOCCORSO PIÙ VICINO."
        else:
            urgency = "GIALLO"
            advice = "Si consiglia una valutazione specialistica cardiologica con urgenza (entro 24-48 ore). Monitorare la pressione arteriosa."

    # 2. Regole per Neurologia
    elif any(k in symptoms_lower for k in ["mal di testa forte", "emicrania improvvisa", "formicolio", "paralisi", "parlare", "vertigini", "confusione"]):
        specialty = "Neurologia"
        if any(k in symptoms_lower for k in ["improvviso", "impossibile parlare", "blocco", "perdita coscienza"]):
            urgency = "ROSSO"
            advice = "ATTENZIONE: Sintomi neurologici acuti ad esordio improvviso. SI CONSIGLIA DI CHIAMARE IMMEDIATAMENTE IL 112 O RECARSI AL PRONTO SOCCORSO."
        else:
            urgency = "GIALLO"
            advice = "Si suggerisce una visita neurologica entro 24-48 ore per escludere complicanze acute. Evitare sforzi."

    # 3. Regole per Ortopedia
    elif any(k in symptoms_lower for k in ["ginocchio", "schiena", "frattura", "trauma", "caduta", "distorsione", "articolare", "osso", "caviglia"]):
        specialty = "Ortopedia"
        if any(k in symptoms_lower for k in ["trauma", "caduta", "gonfio", "non appoggio", "forte dolore"]):
            urgency = "GIALLO"
            advice = "Si consiglia una visita ortopedica o traumatologica a breve. Se si sospetta una frattura esposta o deformità, recarsi in Pronto Soccorso."
        else:
            urgency = "VERDE"
            advice = "Si consiglia riposo, applicazione di ghiaccio localizzato ed eventuale visita ortopedica programmabile in caso di persistenza del sintomo."

    # 4. Regole per Dermatologia
    elif any(k in symptoms_lower for k in ["pelle", "sfogo", "macchia", "prurito", "neo", "eruzione", "orticaria"]):
        specialty = "Dermatologia"
        if "orticaria" in symptoms_lower or "farmaco" in symptoms_lower or "allergica" in symptoms_lower:
            urgency = "GIALLO"
            advice = "Sospetto rash allergico o eruzione cutanea acuta. Se compare difficoltà a respirare o gonfiore a labbra/lingua, chiamare il 112. Altrimenti, visita dermatologica rapida."
        else:
            urgency = "VERDE"
            advice = "Consigliata visita dermatologica di controllo o mappatura dei nei. Evitare l'esposizione al sole e l'uso di cosmetici aggressivi."

    # 5. Regole per Gastroenterologia
    elif any(k in symptoms_lower for k in ["stomaco", "pancia", "reflusso", "bruciore", "gastrico", "nausea", "vomito", "colica"]):
        specialty = "Gastroenterologia"
        if any(k in symptoms_lower for k in ["colica", "dolore lancinante", "vomito sangue"]):
            urgency = "GIALLO"
            advice = "Dolore addominale acuto. Si consiglia valutazione medica rapida. In caso di dolore insopportabile o febbre alta, recarsi in Pronto Soccorso."
        else:
            urgency = "VERDE"
            advice = "Consigliata visita gastroenterologica per reflusso o disturbi digestivi cronici. Seguire una diete leggera ed evitare pasti abbondanti."

    # Aggiungi alla coda dei pazienti per la simulazione
    new_id = f"pat_{random.randint(10, 99)}"
    now = datetime.now().strftime("%H:%M")
    
    new_patient = {
        "id": new_id,
        "name": req.patient_name,
        "age": req.patient_age,
        "symptoms": req.symptoms,
        "specialty": specialty,
        "urgency": urgency,
        "time": now
    }
    
    # Inserisci in cima alla coda per vederlo subito nella dashboard
    TRIAGE_QUEUE.insert(0, new_patient)
    
    return {
        "success": True,
        "patient": new_patient,
        "advice": advice
    }

@app.get("/api/exams")
def get_all_exams():
    return {
        "success": True,
        "exams": [{"id": k, "name": v["name"], "category": v["category"]} for k, v in EXAMS_DATABASE.items()]
    }

@app.get("/api/exams/{exam_id}")
def get_exam_details(exam_id: str):
    exam_key = exam_id.lower()
    if exam_key not in EXAMS_DATABASE:
        raise HTTPException(status_code=404, detail="Esame non trovato")
    return {
        "success": True,
        "exam": EXAMS_DATABASE[exam_key]
    }

@app.get("/api/analytics")
def get_analytics():
    # Ricalcola la distribuzione in tempo reale sulla base della coda
    red_count = sum(1 for p in TRIAGE_QUEUE if p["urgency"] == "ROSSO")
    yellow_count = sum(1 for p in TRIAGE_QUEUE if p["urgency"] == "GIALLO")
    green_count = sum(1 for p in TRIAGE_QUEUE if p["urgency"] == "VERDE")
    
    return {
        "success": True,
        "metrics": {
            "total_triage": len(TRIAGE_QUEUE) + 120, # simulate past cases
            "active_queue": len(TRIAGE_QUEUE),
            "urgency_red": red_count,
            "urgency_yellow": yellow_count,
            "urgency_green": green_count,
            "avg_waiting_time": "12 min",
            "satisfaction_rate": "96.4%"
        },
        "queue": TRIAGE_QUEUE
    }

@app.delete("/api/queue/{patient_id}")
def resolve_patient(patient_id: str):
    global TRIAGE_QUEUE
    initial_len = len(TRIAGE_QUEUE)
    TRIAGE_QUEUE = [p for p in TRIAGE_QUEUE if p["id"] != patient_id]
    if len(TRIAGE_QUEUE) == initial_len:
        raise HTTPException(status_code=404, detail="Paziente non trovato nella coda")
    return {"success": True, "message": "Paziente rimosso dalla coda (chiamata effettuata / preso in carico)"}

# Serve static files from the same directory if index.html is there
try:
    app.mount("/", StaticFiles(directory=".", html=True), name="static")
except Exception:
    pass

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8087, reload=True)
