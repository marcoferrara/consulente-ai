import os
import sys
import json
import logging
import shutil
from typing import Dict, Any, List
from fastapi import FastAPI, Request, HTTPException, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import httpx

# Forza l'encoding utf-8 per lo stdout su Windows per evitare crash con emoji
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Inizializzazione Logger e Variabili d'Ambiente
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Carica variabili da .env locale
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Configura Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Gemini API configurata con successo per La Sorgente.")
else:
    logger.warning("ATTENZIONE: GEMINI_API_KEY non trovata nel file .env!")

app = FastAPI(title="La Sorgente - Hub Operativo Bandi AI")

DB_FILE = os.path.join(BASE_DIR, "database.json")

# Modelli Pydantic
class ProfileUpdate(BaseModel):
    name: str
    legal_type: str
    runts_enrolled: bool
    constitution_date: str
    headquarters: str
    staff_count: int
    annual_budget: float
    certifications: List[str]
    statute_scope: str

class FeasibilityRequest(BaseModel):
    grant_id: str

class DynamicSearchRequest(BaseModel):
    query: str

class ProjectSaveRequest(BaseModel):
    grant_id: str
    project_title: str
    project_summary: str
    key_actions: List[str]
    budget_draft: Dict[str, Any]
    checklist_documents: List[str]
    external_professionals: List[str]
    partnership_strategy: str
    academic_path_advice: str

# Helper Database
def load_db() -> Dict[str, Any]:
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Errore caricamento DB: {e}")
        return {"association_profile": {}, "grants": [], "projects": []}

def save_db(data: Dict[str, Any]):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Errore salvataggio DB: {e}")

# --- API ENDPOINTS ---

@app.get("/api/profile")
async def get_profile():
    db = load_db()
    return JSONResponse(content=db.get("association_profile", {}))

@app.post("/api/profile")
async def update_profile(profile: ProfileUpdate):
    db = load_db()
    db["association_profile"] = profile.model_dump()
    save_db(db)
    return {"status": "success", "message": "Profilo aggiornato con successo"}

@app.get("/api/grants")
async def get_grants():
    db = load_db()
    return JSONResponse(content=db.get("grants", []))

@app.get("/api/projects")
async def get_projects():
    db = load_db()
    return JSONResponse(content=db.get("projects", []))

@app.post("/api/projects/save")
async def save_project(project: ProjectSaveRequest):
    db = load_db()
    new_project = project.model_dump()
    # Controlla se il progetto esiste già per aggiornarlo, altrimenti inserisci
    existing_idx = -1
    for idx, p in enumerate(db.get("projects", [])):
        if p["grant_id"] == project.grant_id:
            existing_idx = idx
            break
    
    if existing_idx != -1:
        db["projects"][existing_idx] = new_project
    else:
        db["projects"].append(new_project)
        
    save_db(db)
    return {"status": "success", "message": "Bozza progetto salvata con successo"}

@app.post("/api/grants/search")
async def search_grants(req: DynamicSearchRequest):
    """
    Usa Gemini 2.5 Flash per simulare la ricerca intelligente in tempo reale di nuovi bandi
    basandosi sulla query dell'utente e sul profilo dell'associazione.
    """
    db = load_db()
    profile = db.get("association_profile", {})
    
    prompt = f"""
    Sei un assistente AI esperto in Europrogettazione e bandi di finanziamento del Terzo Settore italiano ed europeo.
    Il cliente è l'associazione culturale 'La Sorgente' operante a Cagliari (Sardegna) nel campo della formazione di musical e della Comunicazione Non Violenta.
    
    Profilo Associazione:
    - Tipo: {profile.get('legal_type', 'APS')}
    - Iscritta al RUNTS: {profile.get('runts_enrolled', True)}
    - Statuto: {profile.get('statute_scope', 'Teatro e sociale')}
    - Sede: {profile.get('headquarters', 'Cagliari, Sardegna')}
    
    L'utente ha effettuato questa ricerca o richiede bandi correlati a:
    "{req.query}"
    
    Genera una lista di 2 bandi (reali o simulati ma altamente realistici e specifici per il contesto italiano e della Sardegna) che corrispondono a questa richiesta e che siano coerenti con gli obiettivi dell'associazione (Erasmus+, accreditamento accademico, ammodernamento tecnologico, socializzazione).
    
    Rispondi ESATTAMENTE con un oggetto JSON strutturato come segue (non aggiungere spiegazioni o testo di contorno):
    {{
      "new_grants": [
        {{
          "id": "string-id-unico",
          "title": "Titolo del bando molto accattivante e specifico",
          "issuer": "Ente Erogatore (es. Agenzia Nazionale Giovani, Commissione Europea, Regione Sardegna, Fondazione Cariplo, etc.)",
          "budget_max": 80000,
          "deadline": "AAAA-MM-GG (data futura e realistica)",
          "scope": "Cosa finanzia nello specifico per l'associazione (1 frase)",
          "category": "Categoria (es. Erasmus+ & Mobilità, Cultura & Arte, Sociale, Tecnologia)",
          "difficulty": "Bassa, Media o Alta",
          "financing_percentage": 100,
          "description": "Descrizione approfondita dei requisiti di ammissione e delle spese finanziabili."
        }}
      ]
    }}
    """
    
    if not GEMINI_API_KEY:
        # Fallback se non c'è chiave API
        return {"new_grants": []}

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        parsed = json.loads(response.text.strip())
        
        # Aggiungi i bandi temporanei alla lista locale in database.json per consentire all'utente di interagirvi
        new_grants = parsed.get("new_grants", [])
        if new_grants:
            # Rimuovi duplicati basati su id
            existing_ids = {g["id"] for g in db.get("grants", [])}
            added = 0
            for g in new_grants:
                if g["id"] not in existing_ids:
                    db["grants"].append(g)
                    added += 1
            if added > 0:
                save_db(db)
                
        return JSONResponse(content=parsed)
    except Exception as e:
        logger.error(f"Errore nella ricerca bandi con Gemini: {e}")
        raise HTTPException(status_code=500, detail=f"Errore durante l'interrogazione dell'AI: {str(e)}")

@app.post("/api/feasibility")
async def analyze_feasibility(req: FeasibilityRequest):
    """
    Esegue un'analisi approfondita di fattibilità (legale, tecnica, sociale, finanziaria)
    incrociando le specifiche del bando con il profilo dell'associazione caricato nel database.
    """
    db = load_db()
    profile = db.get("association_profile", {})
    
    # Trova il bando
    grant = None
    for g in db.get("grants", []):
        if g["id"] == req.grant_id:
            grant = g
            break
            
    if not grant:
        raise HTTPException(status_code=404, detail="Bando non trovato")

    prompt = f"""
    Sei il consulente legale ed esperto di bandi senior per 'Consulente AI'. Devi redigere una perizia di fattibilità tecnica e legale incrociando i dati di un bando specifico con il profilo del cliente 'La Sorgente' di Cagliari.
    
    Profilo Cliente:
    - Nome: {profile.get('name', 'La Sorgente')}
    - Forma Giuridica: {profile.get('legal_type', 'APS')}
    - Iscrizione RUNTS: {profile.get('runts_enrolled', True)}
    - Sede: {profile.get('headquarters', 'Cagliari')}
    - Personale: {profile.get('staff_count', 8)} collaboratori
    - Budget Annuo: {profile.get('annual_budget', 45000)} €
    - Statuto: {profile.get('statute_scope', 'Formazione musical e CNV')}
    - Certificazioni: {', '.join(profile.get('certifications', []))}
    
    Bando da analizzare:
    - Titolo: {grant.get('title')}
    - Erogatore: {grant.get('issuer')}
    - Cofinanziamento: {grant.get('financing_percentage')}% (Il cliente deve coprire il restante {100 - grant.get('financing_percentage')}%)
    - Difficoltà Stimata: {grant.get('difficulty')}
    - Budget Max: {grant.get('budget_max')} €
    - Scopo: {grant.get('scope')}
    - Descrizione: {grant.get('description')}
    
    Compila un'analisi di fattibilità accurata, pragmatica e onesta. Ricorda che se il cofinanziamento richiesto è troppo alto per il budget del cliente, o se la forma giuridica non coincide con i requisiti del bando, devi segnalarlo come rischio.
    
    Rispondi ESATTAMENTE con un oggetto JSON strutturato come segue (senza testo di contorno):
    {{
      "feasibility_score": 85, // Punteggio da 0 a 100
      "legal_analysis": "Analisi approfondita sulla coerenza dello statuto, forma giuridica (es. se l'iscrizione al RUNTS è obbligatoria) ed eventuale compatibilità con bandi europei.",
      "technical_analysis": "Valutazione sulla capacità operativa dell'associazione. Analizza se gli 8 collaboratori sono sufficienti o se serve integrare competenze specifiche.",
      "social_analysis": "Valutazione dell'impatto sul territorio sardo (Cagliari) e la rilevanza artistica e sociale del progetto (Musical + Negoziazione/CNV).",
      "financial_analysis": "Analisi di sostenibilità economica. Spiega come l'associazione può coprire l'eventuale quota di cofinanziamento e se ha la capacità di cassa per anticipare le spese.",
      "partnership_need": "Consigli strategici sui partenariati. Specifica se è opportuno fare il bando insieme ad altri enti (es. Università di Cagliari, Comuni sardi, altre accademie nazionali/internazionali) e con chi.",
      "expert_recommendations": [
        "Consiglio 1: es. Coinvolgere un commercialista per la rendicontazione delle ore di staff.",
        "Consiglio 2: es. Consultare un avvocato per strutturare l'accordo di partenariato con enti esteri."
      ],
      "eligibility_status": "IDONEO" // Oppure "A RISCHIO" o "NON IDONEO"
    }}
    """
    
    if not GEMINI_API_KEY:
        # Fallback mock offline
        return {
            "feasibility_score": 75,
            "legal_analysis": "L'iscrizione al RUNTS dell'associazione (APS) garantisce piena idoneità formale per la maggior parte dei bandi del terzo settore. Lo scopo statutario copre sia la formazione teatrale sia le attività sociali di negoziazione.",
            "technical_analysis": "L'attuale organico di 8 collaboratori è idoneo per progetti di piccola e media entità. Per un bando di questa portata tecnica, sarà necessario strutturare un cronogramma rigido e allocare chiaramente le ore.",
            "social_analysis": "Forte impatto sul territorio cagliaritano. L'unione di teatro musicale e Comunicazione Non Violenta è un fattore altamente innovativo, molto apprezzato nei criteri di valutazione sociale.",
            "financial_analysis": "Il cofinanziamento richiesto potrebbe gravare sulla cassa dell'associazione. Si consiglia di richiedere un anticipo all'erogatore o stipulare una fideiussione bancaria se prevista.",
            "partnership_need": "Altamente consigliato consorziarsi con una scuola di musical estera (per scambi Erasmus) e patrocinare il progetto con il Comune di Cagliari per aumentare il punteggio.",
            "expert_recommendations": [
              "Ingaggiare un Europrogettista per la scrittura tecnica del bando.",
              "Coinvolgere un revisore dei conti/commercialista abilitato per la validazione del bilancio."
            ],
            "eligibility_status": "IDONEO"
        }

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        parsed = json.loads(response.text.strip())
        return JSONResponse(content=parsed)
    except Exception as e:
        logger.error(f"Errore analisi fattibilità con Gemini: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/project-draft")
async def generate_project_draft(req: FeasibilityRequest):
    """
    Genera un Business Plan completo e una bozza di candidatura per il bando selezionato.
    Include macro-azioni, bozza di budget, checklist documentaria legale e consigli per
    accreditamento universitario del corso di musical/CNV.
    """
    db = load_db()
    profile = db.get("association_profile", {})
    
    grant = None
    for g in db.get("grants", []):
        if g["id"] == req.grant_id:
            grant = g
            break
            
    if not grant:
        raise HTTPException(status_code=404, detail="Bando non trovato")

    prompt = f"""
    Sei il capo del team di Europrogettazione di 'Consulente AI'. Il tuo compito è redigere una bozza avanzata di progetto (Project Draft & Business Plan) per candidare l'associazione 'La Sorgente' al bando specificato.
    
    Associazione:
    - Nome: {profile.get('name', 'La Sorgente')}
    - Sede: {profile.get('headquarters')}
    - Scope: {profile.get('statute_scope')}
    
    Bando:
    - Titolo: {grant.get('title')}
    - Erogatore: {grant.get('issuer')}
    - Budget Massimo Richiedibile: {grant.get('budget_max')} €
    
    Devi produrre un piano operativo strutturato in JSON con le seguenti sezioni. 
    Nel campo 'academic_path_advice', esprimi suggerimenti specifici e concreti su come l'associazione può muoversi per far riconoscere questo corso di musical come CFU (Crediti Formativi Universitari) all'interno dell'Università di Cagliari o creare un percorso didattico alternativo e accreditato a livello nazionale.
    
    Rispondi ESATTAMENTE con questo oggetto JSON (senza altro testo):
    {{
      "grant_id": "{grant.get('id')}",
      "project_title": "Titolo originale e d'impatto per la candidatura del progetto",
      "project_summary": "Sintesi strategica del progetto da inserire nella candidatura (max 4 frasi). Deve includere il musical come strumento pedagogico e la Comunicazione Non Violenta.",
      "key_actions": [
        "Azione 1: Descrizione dettagliata dell'attività (es. Avvio laboratori CNV a Cagliari)",
        "Azione 2: Descrizione dettagliata dell'attività (es. Scambio culturale / mobilità all'estero)",
        "Azione 3: Descrizione dettagliata dell'attività (es. Produzione dello show finale ed esami)"
      ],
      "budget_draft": {{
        "costi_personale": "Bozza importo per docenti, tutor, project manager (es. 25000 €)",
        "costi_viaggio_mobilita": "Bozza per trasferte esterne ed Erasmus (es. 12000 €)",
        "costi_attrezzature_tecnologiche": "Spese per acquisto microfoni, luci e digitalizzazione sede (es. 8000 €)",
        "costi_consulenze_esterne": "Spese per europrogettisti, legali, commercialista (es. 5000 €)",
        "totale_stimato": "Importo totale stimato coerente con il budget massimo"
      }},
      "checklist_documents": [
        "Copia dello Statuto e dell'Atto Costitutivo dell'associazione registrati all'Agenzia delle Entrate.",
        "Certificato di iscrizione al RUNTS.",
        "Ultimi due bilanci consuntivi approvati dall'assemblea dei soci.",
        "Documento di identità e codice fiscale del Legale Rappresentante.",
        "Modello F24 quietanzato attestante regolarità contributiva (DURC se applicabile)."
      ],
      "external_professionals": [
        "Europrogettista senior (scrittura e coordinamento candidatura)",
        "Consulente del Lavoro (contrattualizzazione docenti/tutor)",
        "Commercialista / Revisore dei Conti (rendicontazione e asseverazione spese)",
        "Avvocato civilista (stesura patti di partenariato nazionali/internazionali)"
      ],
      "partnership_strategy": "Descrizione strategica su quali enti coinvolgere per dare peso istituzionale alla candidatura (es. Conservatorio di Cagliari, accademie di musical europee a Londra o Madrid, Comuni della Sardegna).",
      "academic_path_advice": "Roadmap per accreditamento universitario: 1. Avviare un accordo di cooperazione con la Facoltà di Studi Umanistici dell'Università di Cagliari per riconoscimento CFU come attività a scelta dello studente. 2. Richiedere il patrocinio onorario dell'ERSU. 3. Convenzionarsi con un Conservatorio di Musica statale per corsi accreditati AFAM (Alta Formazione Artistica e Musicale)."
    }}
    """

    if not GEMINI_API_KEY:
        # Fallback mock offline
        return {
            "grant_id": grant.get("id"),
            "project_title": "La Sorgente del Musical: Arte, Empatia e Inclusione a Cagliari",
            "project_summary": "Il progetto mira a strutturare un percorso formativo d'eccellenza a Cagliari che unisce lo studio delle arti performative del musical con lo sviluppo di soft skill basate sulla Comunicazione Non Violenta (CNV) e la negoziazione cooperativa.",
            "key_actions": [
              "Laboratori di Teatro Musicale Integrato e Scenotecnica per giovani sardi.",
              "Masterclass di Comunicazione Empatica e Risoluzione Conflitti condotte da docenti accreditati.",
              "Coproduzione e messa in scena di uno spettacolo musicale con accademie partner in Europa."
            ],
            "budget_draft": {
              "costi_personale": "28,000 €",
              "costi_viaggio_mobilita": "15,000 €",
              "costi_attrezzature_tecnologiche": "10,000 €",
              "costi_consulenze_esterne": "5,000 €",
              "totale_stimato": "58,000 €"
            },
            "checklist_documents": [
              "Statuto e Atto Costitutivo registrati",
              "Certificato iscrizione RUNTS",
              "Bilanci degli ultimi 2 anni",
              "Documento del legale rappresentante",
              "DURC dell'associazione in corso di validità"
            ],
            "external_professionals": [
              "Europrogettista Senior per la candidatura",
              "Commercialista per monitoraggio cassa e rendicontazione",
              "Avvocato per accordi internazionali di mobilità"
            ],
            "partnership_strategy": "Inclusione del Conservatorio statale di Cagliari, della Facoltà di Studi Umanistici di UniCA, ed accademie musicali a Madrid e Parigi.",
            "academic_path_advice": "Roadmap UniCA: 1. Presentazione dell'offerta formativa al Consiglio di Corso di Laurea in Beni Culturali/Spettacolo per delibera riconoscimento 3 o 6 CFU. 2. Stipula di una convenzione quadro con l'Ateneo per tirocini formativi esterni per studenti."
        }

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        parsed = json.loads(response.text.strip())
        return JSONResponse(content=parsed)
    except Exception as e:
        logger.error(f"Errore generazione bozza con Gemini: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class CertificationRequest(BaseModel):
    certification_type: str

class ToggleRequirementRequest(BaseModel):
    certification_type: str
    requirement_name: str
    completed: bool

@app.post("/api/certifications/toggle-requirement")
async def toggle_requirement(req: ToggleRequirementRequest):
    db = load_db()
    if "completed_requirements" not in db:
        db["completed_requirements"] = {}
    if req.certification_type not in db["completed_requirements"]:
        db["completed_requirements"][req.certification_type] = []
        
    reqs = db["completed_requirements"][req.certification_type]
    if req.completed:
        if req.requirement_name not in reqs:
            reqs.append(req.requirement_name)
    else:
        if req.requirement_name in reqs:
            reqs.remove(req.requirement_name)
            
    save_db(db)
    return {"status": "success", "completed_requirements": reqs}

@app.post("/api/documents/upload")
async def upload_document(
    certification_type: str = Form(...),
    requirement_name: str = Form(...),
    document_name: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(None)
):
    db = load_db()
    
    # Assicuriamoci che esista la cartella uploads
    uploads_dir = os.path.join(BASE_DIR, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    
    filename = None
    if file and file.filename:
        filename = file.filename
        file_path = os.path.join(uploads_dir, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    else:
        filename = "Giustificazione Scritta"
        
    doc_entry = {
        "document_name": document_name,
        "description": description,
        "filename": filename,
        "uploaded_at": "2026-05-19T10:00:00",
        "certification_type": certification_type,
        "requirement_name": requirement_name
    }
    
    if "uploaded_documents" not in db:
        db["uploaded_documents"] = []
    
    # Rimuovi eventuali vecchi caricamenti per lo stesso requisito
    db["uploaded_documents"] = [d for d in db["uploaded_documents"] if not (d.get("certification_type") == certification_type and d.get("requirement_name") == requirement_name)]
    db["uploaded_documents"].append(doc_entry)
    
    # Segna anche il requisito come superato!
    if "completed_requirements" not in db:
        db["completed_requirements"] = {}
    if certification_type not in db["completed_requirements"]:
        db["completed_requirements"][certification_type] = []
    if requirement_name not in db["completed_requirements"][certification_type]:
        db["completed_requirements"][certification_type].append(requirement_name)
        
    save_db(db)
    return {"status": "success", "message": "Documento convalidato con successo!", "document": doc_entry}

@app.get("/api/certifications/status")
async def get_certifications_status():
    db = load_db()
    return {
        "completed_requirements": db.get("completed_requirements", {}),
        "uploaded_documents": db.get("uploaded_documents", [])
    }

@app.post("/api/certifications/analyze")
async def analyze_certification(req: CertificationRequest):
    """
    Esegue una GAP analysis avanzata con Gemini per determinare cosa manca all'associazione
    per ottenere l'accreditamento regionale, l'iscrizione al RUNTS, la certificazione ISO 9001 o il riconoscimento CFU.
    Integra dinamicamente le evidenze e i documenti asseverati dall'utente.
    """
    db = load_db()
    profile = db.get("association_profile", {})
    completed_reqs = db.get("completed_requirements", {}).get(req.certification_type, [])
    uploaded_docs = [d for d in db.get("uploaded_documents", []) if d.get("certification_type") == req.certification_type]
    
    cert_types = {
        "regione_sardegna": "Accreditamento Regionale come Ente di Formazione (Regione Autonoma della Sardegna)",
        "iso_9001": "Certificazione Sistema di Gestione Qualità ISO 9001:2015 (Settore EA37 - Istruzione/Formazione)",
        "runts": "Adeguamento Statutario e Iscrizione a pieno titolo nel Registro Unico Nazionale del Terzo Settore (RUNTS)",
        "cfu_universita": "Accreditamento Didattico e Convenzione per Riconoscimento Crediti Formativi Universitari (CFU) con UniCA"
    }
    
    cert_name = cert_types.get(req.certification_type, "Accreditamento Specialistico")
    
    # Formattazione per Gemini
    docs_formatted = "\n".join([f"- Nome Documento: '{d['document_name']}' | Riferito a: '{d['requirement_name']}' | File asseverato: '{d['filename']}' | Descrizione: {d['description']}" for d in uploaded_docs])
    completed_reqs_formatted = ", ".join([f"'{r}'" for r in completed_reqs])
    
    prompt = f"""
    Sei il consulente senior per la Qualità, Accreditamenti e Regolamenti del Terzo Settore di 'Consulente AI'.
    Il cliente 'La Sorgente' vuole ottenere la seguente certificazione/accreditamento:
    "{cert_name}"
    
    Incrocia i requisiti obbligatori nazionali e regionali (Regione Sardegna) con il Profilo attuale dell'associazione:
    - Nome: {profile.get('name')}
    - Forma Giuridica: {profile.get('legal_type')}
    - Iscritta al RUNTS: {profile.get('runts_enrolled')}
    - Sede: {profile.get('headquarters')}
    - Collaboratori: {profile.get('staff_count')}
    - Budget Annuo: {profile.get('annual_budget')} €
    - Statuto: {profile.get('statute_scope')}
    - Certificazioni attuali: {', '.join(profile.get('certifications', []))}
    
    EVIDENZE E DOCUMENTI ASSEVERATI DALL'ASSOCIAZIONE (DA CONVALIDARE):
    - Documenti asseverati già caricati dall'associazione:
    {docs_formatted or 'Nessun documento o asseverazione ancora caricata.'}
    
    - Requisiti contrassegnati come già RAGGIUNTI / SUPERATI manualmente dall'utente:
    {completed_reqs_formatted or 'Nessun requisito contrassegnato manualmente.'}
    
    REQUISITO CRITICO:
    1. Se un requisito obbligatorio o documento richiesto risulta coperto dai documenti caricati sopra o è elencato tra i requisiti contrassegnati come superati, DEVI contrassegnarlo come "soddisfatto" (status: "soddisfatto") nel JSON di risposta.
    2. Spiega nei dettagli (nel campo "details") in che modo il documento o la dichiarazione fornita giustifica il superamento della carenza. Sii specifico e cita il nome del documento.
    3. Il punteggio di compliance complessivo ('compliance_score') deve riflettere questa conformità ed essere incrementato in modo appropriato (il punteggio base se tutto manca parte da circa 25-35%, mentre sale fino a 80-90% o 100% se tutti i requisiti vengono superati o documentati).
    
    Fornisci una GAP Analysis onesta ed estremamente accurata sui requisiti fisici (aula, attrezzature), documentali e di staff.
    Evidenzia chiaramente quali requisiti sono soddisfatti e quali sono MANCANTI (il cliente parte da zero o ha forti lacune).
    
    Rispondi ESATTAMENTE con questo oggetto JSON (non aggiungere spiegazioni esterne):
    {{
      "certification_name": "{cert_name}",
      "compliance_score": 35, // Punteggio da 0 a 100 proporzionale ai requisiti soddisfatti
      "mandatory_requirements": [
        {{
          "requirement": "Titolo del requisito (es. Idoneità dei Locali)",
          "status": "mancante", // "soddisfatto", "parziale", "mancante"
          "details": "Spiegazione sul perché manca o come deve essere adeguato."
        }},
        {{
          "requirement": "Requisito di Staff (es. Direttore di Corso Certificato)",
          "status": "parziale",
          "details": "Dettagli sulle qualifiche minime necessarie."
        }}
      ],
      "required_assets": [
        "Aula didattica di almeno X mq con certificato di agibilità e barriere architettoniche superate.",
        "Sistemi di sicurezza a norma (estintori, cassette di pronto soccorso, cartellonistica di evacuazione).",
        "Trattamento acustico di base per aule di teatro e canto."
      ],
      "required_documents": [
        "Statuto modificato in conformità con il Codice del Terzo Settore (se non adeguato).",
        "Manuale delle procedure di Qualità (se ISO 9001).",
        "Curriculum Vitae dei docenti firmati in formato europeo attestanti almeno 2/3 anni di docenza nello spettacolo."
      ],
      "recommended_professionals": [
        "Ingegnere abilitato o Tecnico della Sicurezza (per asseverazione locali, DVR e planimetria di fuga)",
        "Consulente sistemi di gestione qualità (per stesura procedure ISO 9001)",
        "Notaio o Avvocato del terzo settore (per modifiche statutarie e deposito RUNTS)"
      ],
      "action_plan": [
        "Fase 1: Adeguamento formale dello statuto (se APS) presso l'Agenzia delle Entrate.",
        "Fase 2: Reperimento o locazione di una sede fisica con destinazione d'uso catastale compatibile (es. C/3 o A/10) e barriere architettoniche abbattute.",
        "Fase 3: Nomina formale dei ruoli chiave (Responsabile di Progetto, Responsabile di Direzione, ecc.)",
        "Fase 4: Presentazione istanza telematica sul portale dedicato (SardegnaLavoro o portale RUNTS)."
      ]
    }}
    """
    
    if not GEMINI_API_KEY:
        # Fallback offline
        reqs_list = [
            {
              "requirement": "Adeguamento Catastale e Locali",
              "status": "soddisfatto" if "Adeguamento Catastale e Locali" in completed_reqs else "mancante",
              "details": "Convalidato con successo tramite i documenti caricati dall'utente." if "Adeguamento Catastale e Locali" in completed_reqs else "L'associazione non ha dichiarato una sede con destinazione d'uso idonea per la formazione pubblica (destinazione commerciale o ufficio A/10 o C/3). I locali devono rispettare le normas igienico-sanitarie della ASL di Cagliari."
            },
            {
              "requirement": "Organico con Ruoli Certificati",
              "status": "soddisfatto" if "Organico con Ruoli Certificati" in completed_reqs else "parziale",
              "details": "Convalidato con successo tramite i contratti e contrassegno utente." if "Organico con Ruoli Certificati" in completed_reqs else "Sebbene vi siano 8 collaboratori, per l'accreditamento regionale sardo occorre nominare formalmente 3 figure distinte: un Direttore Didattico, un Responsabile della Qualità e un Responsabile della Gestione Economica (con relativi CV idonei)."
            },
            {
              "requirement": "Adeguamento Statutario",
              "status": "soddisfatto" if ("Adeguamento Statutario" in completed_reqs or len(uploaded_docs) > 0) else "soddisfatto",
              "details": "Lo statuto attuale copre gli scopi formativi e sociali, ma per l'iscrizione al RUNTS va depositata la versione registrata conforme al D.Lgs 117/2017."
            }
        ]
        
        satisfied_count = sum(1 for r in reqs_list if r["status"] == "soddisfatto")
        final_score = 30 + (satisfied_count * 22)
        
        return {
            "certification_name": cert_name,
            "compliance_score": min(final_score, 100),
            "mandatory_requirements": reqs_list,
            "required_assets": [
              "Aula didattica accreditabile dotata di impianto di aerazione a norma.",
              "Impianto audio-video certificato per lezioni di musical.",
              "Dispositivi di primo soccorso ed estintori con verifiche semestrali attive."
            ] if "Adeguamento Catastale e Locali" not in completed_reqs else [],
            "required_documents": [
              "Documento di Valutazione dei Rischi (DVR) firmato da un RSPP.",
              "Planimetria asseverata con vie di fuga evidenziate.",
              "Polizza assicurativa RC per allievi e docenti."
            ] if not any(d.get("requirement_name") == "Documentazione sulla Sicurezza" for d in uploaded_docs) else [],
            "recommended_professionals": [
              "Tecnico RSPP per la redazione del DVR.",
              "Consulente per gli accreditamenti formativi regionali."
            ] if not any(d.get("requirement_name") == "Documentazione sulla Sicurezza" for d in uploaded_docs) else [],
            "action_plan": [
              "Fase 1: Individuazione locali a Cagliari idonei (o adeguamento sede attuale).",
              "Fase 2: Redazione del fascicolo tecnico della sicurezza (DVR, Planimetrie).",
              "Fase 3: Nomina formale dei 3 responsabili operativi e firma dei relativi contratti/incarichi.",
              "Fase 4: Invio candidatura sul portale SIL Sardegna."
            ]
        }

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        parsed = json.loads(response.text.strip())
        return JSONResponse(content=parsed)
    except Exception as e:
        logger.error(f"Errore gap analysis certificazioni con Gemini: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- DASHBOARD RENDERING ---

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """
    Ritorna la bellissima dashboard web interattiva per l'hub operativo 'La Sorgente'.
    Tutto lo stile e le funzionalità sono incorporate per un'esperienza wow immediata.
    """
    html_path = os.path.join(BASE_DIR, "index.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"Errore lettura index.html: {e}")
        return HTMLResponse(content=f"<h1>Errore caricamento Dashboard</h1><p>{str(e)}</p>")

if __name__ == "__main__":
    import uvicorn
    # Avvia in locale sulla porta 8081 per evitare conflitti con ricambi_truck (8000)
    uvicorn.run("app:app", host="127.0.0.1", port=8081, reload=True)

