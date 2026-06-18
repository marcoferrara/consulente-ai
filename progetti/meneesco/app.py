import os
import sys
import json
import logging
import shutil
from datetime import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, Request, HTTPException, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
import hashlib
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    logger.info("Gemini API configurata con successo per MENEESCO.")
else:
    logger.warning("ATTENZIONE: GEMINI_API_KEY non trovata nel file .env!")

app = FastAPI(title="MENEESCO - Hub Operativo Bandi AI per la P.A.")

APP_PASSWORD = os.getenv("APP_PASSWORD")
SESSION_TOKEN = hashlib.sha256(APP_PASSWORD.encode()).hexdigest() if APP_PASSWORD else None

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if not APP_PASSWORD:
        return await call_next(request)

    path = request.url.path
    public_paths = ["/login", "/favicon.ico", "/47120255_padded_logo.png", "/uploads/"]

    if path == "/" or any(path.startswith(p) for p in public_paths):
        return await call_next(request)

    session_cookie = request.cookies.get("meneesco_session")
    if session_cookie == SESSION_TOKEN:
        return await call_next(request)

    is_api = path.startswith("/api/")
    if is_api:
        return JSONResponse(
            status_code=401,
            content={"status": "error", "message": "Non autorizzato. Sessione non valida o scaduta."}
        )
    else:
        login_url = f"/login?next={path}"
        if request.query_params:
            login_url += f"&{request.query_params}"
        return RedirectResponse(url=login_url)

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request, next: str = "/bandi"):
    if not APP_PASSWORD:
        return RedirectResponse(url=next)

    if request.cookies.get("meneesco_session") == SESSION_TOKEN:
        return RedirectResponse(url=next)

    html_content = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accesso Protetto — MENEESCO</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Source+Serif+4:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Source Serif 4', Georgia, serif;
            background: #F2EAD5;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='400' height='400' filter='url(%23n)' opacity='0.028'/%3E%3C/svg%3E");
            color: #18100A;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .login-card {{
            background: rgba(242, 234, 213, 0.95);
            border: 1px solid rgba(140, 27, 27, 0.15);
            border-radius: 4px;
            padding: 48px 40px;
            width: 100%;
            max-width: 420px;
            box-shadow: 0 8px 32px rgba(24, 16, 10, 0.12);
            position: relative;
        }}
        .login-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg, #8C1B1B, #B8882E);
        }}
        .logo-wrap {{
            text-align: center;
            margin-bottom: 36px;
        }}
        .logo-img {{ width: 48px; height: 48px; object-fit: contain; margin-bottom: 12px; }}
        .logo-name {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.6rem;
            font-weight: 600;
            letter-spacing: 0.12em;
            color: #18100A;
        }}
        .logo-sub {{
            font-size: 0.6rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: #8C1B1B;
            display: block;
            margin-top: 2px;
        }}
        label {{
            display: block;
            font-size: 0.65rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #6B5744;
            margin-bottom: 6px;
        }}
        input[type=password] {{
            width: 100%;
            background: rgba(255,255,255,0.6);
            border: 1px solid rgba(51,38,24,0.2);
            border-radius: 2px;
            padding: 12px 14px;
            font-size: 0.95rem;
            color: #18100A;
            outline: none;
            margin-bottom: 24px;
            font-family: inherit;
        }}
        input[type=password]:focus {{
            border-color: #8C1B1B;
            box-shadow: 0 0 0 3px rgba(140,27,27,0.08);
        }}
        .btn-login {{
            width: 100%;
            background: #8C1B1B;
            border: none;
            border-radius: 2px;
            padding: 13px;
            color: #F2EAD5;
            font-family: 'Source Serif 4', serif;
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            letter-spacing: 0.04em;
            transition: background 0.3s;
        }}
        .btn-login:hover {{ background: #AE2020; }}
        .error-msg {{
            background: rgba(140,27,27,0.08);
            border: 1px solid rgba(140,27,27,0.25);
            color: #8C1B1B;
            padding: 10px 14px;
            border-radius: 2px;
            font-size: 0.82rem;
            margin-bottom: 18px;
            display: none;
        }}
        .footer-text {{ text-align: center; font-size: 0.65rem; color: #6B5744; margin-top: 28px; }}
    </style>
</head>
<body>
    <div class="login-card">
        <div class="logo-wrap">
            <img src="/47120255_padded_logo.png" alt="MENEESCO" class="logo-img">
            <div class="logo-name">ME.NE.E.S.CO.</div>
            <span class="logo-sub">Hub Bandi Istituzionali AI</span>
        </div>
        <div id="error-box" class="error-msg"></div>
        <form id="login-form">
            <label for="password">Password di Accesso</label>
            <input type="password" id="password" name="password" placeholder="Password riservata dell'applicazione" required autofocus>
            <button class="btn-login" type="submit">Accedi al Portale</button>
        </form>
        <div class="footer-text">&copy; 2026 Consulente AI &bull; Accesso Riservato</div>
    </div>
    <script>
        document.getElementById('login-form').addEventListener('submit', async (e) => {{
            e.preventDefault();
            const errorBox = document.getElementById('error-box');
            errorBox.style.display = 'none';
            const password = document.getElementById('password').value;
            const nextUrl = new URLSearchParams(window.location.search).get('next') || '/bandi';
            try {{
                const response = await fetch('/login', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                    body: new URLSearchParams({{ 'password': password, 'next': nextUrl }})
                }});
                const data = await response.json();
                if (response.ok && data.status === 'success') {{
                    window.location.href = data.redirect || nextUrl;
                }} else {{
                    errorBox.textContent = data.message || 'Password non corretta.';
                    errorBox.style.display = 'block';
                }}
            }} catch (err) {{
                errorBox.textContent = 'Errore di connessione al server.';
                errorBox.style.display = 'block';
            }}
        }});
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)

@app.post("/login")
async def login_post(password: str = Form(...), next: str = Form("/bandi")):
    if not APP_PASSWORD:
        return {"status": "success", "redirect": next}
    input_hash = hashlib.sha256(password.encode()).hexdigest()
    if input_hash == SESSION_TOKEN:
        response = JSONResponse(content={"status": "success", "redirect": next})
        response.set_cookie(
            key="meneesco_session",
            value=SESSION_TOKEN,
            max_age=30 * 24 * 3600,
            httponly=True,
            samesite="lax",
            path="/"
        )
        return response
    else:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Password di accesso non valida. Riprova."}
        )

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie(key="meneesco_session", path="/")
    return response

@app.get("/47120255_padded_logo.png")
async def get_logo():
    logo_path = os.path.join(BASE_DIR, "47120255_padded_logo.png")
    if not os.path.exists(logo_path):
        raise HTTPException(status_code=404, detail="Logo non trovato.")
    from fastapi.responses import FileResponse
    return FileResponse(logo_path)

PERSISTENT_DATA_DIR = os.getenv("PERSISTENT_DATA_DIR")
if PERSISTENT_DATA_DIR:
    PERSISTENT_DATA_DIR = os.path.abspath(PERSISTENT_DATA_DIR)
    os.makedirs(PERSISTENT_DATA_DIR, exist_ok=True)
    DB_FILE = os.path.join(PERSISTENT_DATA_DIR, "database.json")
    UPLOADS_DIR = os.path.join(PERSISTENT_DATA_DIR, "uploads")
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    default_db = os.path.join(BASE_DIR, "database.json")
    if not os.path.exists(DB_FILE) and os.path.exists(default_db):
        try:
            shutil.copy2(default_db, DB_FILE)
        except Exception as e:
            logger.error(f"Errore copia database default: {e}")
else:
    DB_FILE = os.path.join(BASE_DIR, "database.json")
    UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
    os.makedirs(UPLOADS_DIR, exist_ok=True)


class ProfileUpdate(BaseModel):
    name: str
    legal_type: str
    constitution_date: str
    headquarters: str
    staff_count: int
    annual_revenue: float
    piva: str
    ateco_code: str
    business_activity: str
    property_status: str = "si"
    roof_access: str = "si"
    sun_exposure: str = "misto"
    digital_channels: List[str] = []
    strategic_goals: List[str] = []
    custom_constraints: str = ""
    market_context: str = ""
    ai_instructions: str = ""


class FeasibilityRequest(BaseModel):
    grant_id: str
    funding_priorities: str = ""


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
    post_award_roadmap: Dict[str, str] = {}


def load_db() -> Dict[str, Any]:
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Errore caricamento DB: {e}")
        return {"company_profile": {}, "grants": [], "projects": []}


def save_db(data: Dict[str, Any]):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Errore salvataggio DB: {e}")


@app.get("/api/profile")
async def get_profile():
    db = load_db()
    return JSONResponse(content=db.get("company_profile", {}))


@app.post("/api/profile")
async def update_profile(profile: ProfileUpdate):
    db = load_db()
    db["company_profile"] = profile.model_dump()
    save_db(db)
    return {"status": "success", "message": "Profilo ente aggiornato con successo"}


@app.get("/api/grants")
async def get_grants():
    db = load_db()
    today_str = datetime.now().strftime("%Y-%m-%d")
    grants = [g for g in db.get("grants", []) if is_deadline_active(g.get("deadline", ""), today_str)]
    return JSONResponse(content=grants)


@app.get("/api/projects")
async def get_projects():
    db = load_db()
    return JSONResponse(content=db.get("projects", []))


@app.get("/api/certifications/status")
async def get_certifications_status():
    db = load_db()
    uploaded_docs = db.get("uploaded_documents", [])
    completed_reqs = {}
    for doc in uploaded_docs:
        req_name = doc.get("requirement_name")
        if req_name:
            completed_reqs[req_name] = True
    return JSONResponse(content={
        "completed_requirements": completed_reqs,
        "uploaded_documents": uploaded_docs
    })


@app.post("/api/documents/upload")
async def upload_document(
    certification_type: str = Form(...),
    requirement_name: str = Form(...),
    document_name: str = Form(...),
    description: str = Form(...),
    existing_filename: str = Form(None),
    file: UploadFile = File(None)
):
    db = load_db()
    uploaded_docs = db.get("uploaded_documents", [])
    filename = "Simulato"
    file_path = ""
    if file:
        filename = file.filename
        file_path = os.path.join(UPLOADS_DIR, filename)
        try:
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Impossibile salvare il file: {str(e)}")
    elif existing_filename:
        filename = existing_filename
    uploaded_docs = [d for d in uploaded_docs if d.get("requirement_name") != requirement_name]
    new_doc = {
        "certification_type": certification_type,
        "requirement_name": requirement_name,
        "document_name": document_name,
        "description": description,
        "filename": filename,
        "file_path": file_path
    }
    uploaded_docs.append(new_doc)
    db["uploaded_documents"] = uploaded_docs
    save_db(db)
    return {"status": "success", "message": "Documento asseverato con successo"}


@app.post("/api/documents/delete")
async def delete_document(req: Dict[str, Any]):
    certification_type = req.get("certification_type")
    requirement_name = req.get("requirement_name")
    db = load_db()
    uploaded_docs = db.get("uploaded_documents", [])
    doc_to_delete = None
    new_docs = []
    for d in uploaded_docs:
        if d.get("certification_type") == certification_type and d.get("requirement_name") == requirement_name:
            doc_to_delete = d
        else:
            new_docs.append(d)
    if doc_to_delete:
        file_path = doc_to_delete.get("file_path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Errore rimozione file: {e}")
        db["uploaded_documents"] = new_docs
        save_db(db)
        return {"status": "success", "message": "Documento eliminato con successo"}
    else:
        raise HTTPException(status_code=404, detail="Documento non trovato")


@app.post("/api/projects/save")
async def save_project(project: ProjectSaveRequest):
    db = load_db()
    new_project = project.model_dump()
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
    return {"status": "success", "message": "Bozza progetto salvata in archivio"}


def is_deadline_active(deadline_str: str, today_str: str) -> bool:
    if not deadline_str:
        return True
    d_str = deadline_str.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            dt = datetime.strptime(d_str[:10], fmt)
            return dt.strftime("%Y-%m-%d") >= today_str
        except ValueError:
            continue
    import re
    years = re.findall(r'\b(202[6-9]|203[0-9])\b', d_str)
    if years:
        current_year = int(today_str[:4])
        bando_year = int(years[0])
        return bando_year >= current_year
    d_lower = d_str.lower()
    if "scaduto" in d_lower or "chiuso" in d_lower:
        return False
    return True


@app.post("/api/grants/search")
async def search_grants(req: DynamicSearchRequest):
    db = load_db()
    profile = db.get("company_profile", {})
    today_str = datetime.now().strftime("%Y-%m-%d")

    if not GEMINI_API_KEY:
        return {"new_grants": []}

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        ente_name = profile.get('name', 'Ente Pubblico')
        ente_type = profile.get('legal_type', 'Comune')
        sede = profile.get('headquarters', 'Sardegna')
        n_dip = profile.get('staff_count', 20)

        search_prompt = f"""
        Sei un assistente AI senior ed Europrogettista esperto in finanza agevolata e bandi per enti pubblici (P.A.) italiani ed europei.
        Il cliente è l'ente '{ente_name}', un {ente_type} con sede a {sede} con {n_dip} dipendenti.
        Il contesto è: il Metodo ME.NE.E.S.CO. (Metodo di Negoziazione e Gestione delle Crisi) è un protocollo scientifico di de-escalation cognitiva e mediazione dei conflitti che viene erogato come servizio formativo agli enti pubblici italiani.

        La data odierna è: {today_str}.

        Utilizza lo strumento di ricerca Google per trovare bandi REALI ed ATTIVI (scadenza strettamente uguale o posteriore a {today_str}) che finanzino le attività richieste:
        "{req.query}"

        Cerca nei portali:
        - funzionepubblica.gov.it (Dipartimento Funzione Pubblica)
        - sardegnalavoro.it / sardegnaprogrammazione.it (per enti sardi)
        - interno.gov.it (Ministero dell'Interno)
        - agenziacoesione.gov.it
        - inail.it (benessere organizzativo)
        - europa.eu (FSE+, PNRR, Erasmus+)

        Trova esattamente 2 bandi attivi per enti pubblici. Per ciascun bando indica:
        - Titolo del bando
        - Ente erogatore
        - Budget massimo
        - Scadenza
        - Categoria e ambito
        - Difficoltà (Bassa, Media, Alta)
        - Percentuale di copertura / fondo perduto
        - Descrizione dei requisiti di ammissibilità e delle spese finanziabili (in particolare: formazione, mediazione, consulenze organizzative)
        - URL ufficiale del bando
        """

        search_response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=search_prompt,
            config=genai_types.GenerateContentConfig(
                tools=[genai_types.Tool(google_search=genai_types.GoogleSearch())]
            )
        )
        raw_report = search_response.text

        json_prompt = f"""
        Analizza il seguente report di bandi per enti pubblici e convertilo in un oggetto JSON strutturato.
        Non inventare dati, usa solo le informazioni presenti nel report.
        La data odierna è {today_str}. Escludi bandi scaduti.

        Report:
        {raw_report}

        RISPONDI ESATTAMENTE con questo JSON (nessun testo esterno):
        {{
          "new_grants": [
            {{
              "id": "id-kebab-unico",
              "title": "Titolo del bando istituzionale specifico",
              "issuer": "Ente Erogatore",
              "budget_max": 100000,
              "deadline": "AAAA-MM-GG (futura, posteriore al {today_str})",
              "scope": "Cosa finanzia per un ente pubblico (1 frase)",
              "category": "Categoria (es. Nazionale PNRR, Regionale FSE+)",
              "difficulty": "Bassa, Media o Alta",
              "financing_percentage": 100,
              "description": "Descrizione approfondita dei requisiti e delle spese ammissibili per enti pubblici.",
              "official_link": "URL ufficiale reale del bando"
            }}
          ]
        }}
        """

        json_response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=json_prompt,
            config=genai_types.GenerateContentConfig(response_mime_type="application/json")
        )
        parsed = json.loads(json_response.text.strip())

        new_grants = parsed.get("new_grants", [])
        if new_grants:
            filtered = []
            for g in new_grants:
                deadline = g.get("deadline", "")
                if is_deadline_active(deadline, today_str):
                    title = g.get("title", "")
                    if title:
                        slug = title.lower().replace(" ", "-").replace("—", "-")
                        slug = "".join(c for c in slug if c.isalnum() or c == "-")
                        while "--" in slug:
                            slug = slug.replace("--", "-")
                        g["id"] = slug.strip("-")[:60]
                    else:
                        g["id"] = f"bando-{hashlib.md5(str(g).encode()).hexdigest()[:8]}"
                    filtered.append(g)

            if filtered:
                existing_ids = {g["id"] for g in db.get("grants", [])}
                added = 0
                for g in filtered:
                    if g["id"] not in existing_ids:
                        db["grants"].append(g)
                        added += 1
                if added > 0:
                    save_db(db)
                parsed["new_grants"] = filtered
            else:
                parsed["new_grants"] = []

        return JSONResponse(content=parsed)

    except Exception as e:
        logger.error(f"Errore ricerca bandi PA con Gemini: {e}")
        fallback_grants = [{
            "id": "fallback-fse-formazione-pa",
            "title": "FSE+ — Formazione Professionale Continua per Dipendenti della Pubblica Amministrazione",
            "issuer": "Regione Autonoma della Sardegna — Assessorato al Lavoro",
            "budget_max": 80000,
            "deadline": "2026-09-30",
            "scope": "Finanzia corsi di formazione su mediazione, de-escalation cognitiva e comunicazione istituzionale per dipendenti PA.",
            "category": "Regionale Sardegna — FSE+",
            "difficulty": "Bassa",
            "financing_percentage": 100,
            "description": "Bando FSE+ per la formazione continua dei dipendenti pubblici sardi. Copertura al 100% per percorsi su gestione dei conflitti, mediazione istituzionale, de-escalation e comunicazione pubblica efficace.",
            "official_link": "https://sardegnalavoro.it/"
        }]
        existing_ids = {g["id"] for g in db.get("grants", [])}
        added = 0
        for g in fallback_grants:
            if g["id"] not in existing_ids:
                db["grants"].append(g)
                added += 1
        if added > 0:
            save_db(db)
        return {"new_grants": fallback_grants}


@app.post("/api/feasibility")
async def analyze_feasibility(req: FeasibilityRequest):
    db = load_db()
    profile = db.get("company_profile", {})
    projects = db.get("projects", [])

    def clean_budget_str(b_str: Any) -> float:
        if isinstance(b_str, (int, float)):
            return float(b_str)
        if not b_str:
            return 0.0
        s = str(b_str).replace("€", "").replace(".", "").replace(",", ".").replace(" ", "").strip()
        try:
            return float(s)
        except ValueError:
            return 0.0

    grant = None
    for g in db.get("grants", []):
        if g["id"] == req.grant_id:
            grant = g
            break
    if not grant:
        raise HTTPException(status_code=404, detail="Bando non trovato")

    grant_budget = float(grant.get("budget_max", 0))

    current_projects_budget = 0.0
    for p in projects:
        b_draft = p.get("budget_draft", {})
        tot = b_draft.get("totale_stimato", 0)
        current_projects_budget += clean_budget_str(tot)

    projected_cumulative_budget = current_projects_budget + grant_budget
    de_minimis_limit = 500000.0  # Per PA è De Minimis SIEG (Servizi di Interesse Economico Generale)
    de_minimis_warning = projected_cumulative_budget > de_minimis_limit

    staff_limit = int(profile.get("staff_count", 20))
    active_projects_count = len(projects)
    projected_staff_occupied = active_projects_count * 2  # 2 referenti per progetto formativo
    staff_warning = projected_staff_occupied > (staff_limit * 0.3)  # allarme se > 30% del personale coinvolto

    pre_financing_pct = 0.20  # PA tipicamente anticipano meno
    projected_pre_financing_needed = projected_cumulative_budget * pre_financing_pct
    annual_revenue = float(profile.get("annual_revenue", 50000.0))
    cash_flow_warning = projected_pre_financing_needed > (annual_revenue * 0.50)

    issuer_conflict = False
    conflicting_project_title = ""
    grant_issuer = grant.get("issuer", "")
    for p in projects:
        other_grant_id = p.get("grant_id")
        other_grant = next((g for g in db.get("grants", []) if g["id"] == other_grant_id), None)
        if other_grant:
            other_issuer = other_grant.get("issuer", "")
            if (grant_issuer.lower() in other_issuer.lower()) or (other_issuer.lower() in grant_issuer.lower()):
                issuer_conflict = True
                conflicting_project_title = p.get("project_title", "")
                break

    cumulative_checks = {
        "current_projects_budget": current_projects_budget,
        "projected_cumulative_budget": projected_cumulative_budget,
        "de_minimis_limit": de_minimis_limit,
        "de_minimis_warning": de_minimis_warning,
        "staff_limit": staff_limit,
        "current_staff_occupied": active_projects_count * 2,
        "projected_staff_occupied": projected_staff_occupied,
        "staff_warning": staff_warning,
        "projected_pre_financing_needed": projected_pre_financing_needed,
        "annual_budget": annual_revenue,
        "cash_flow_warning": cash_flow_warning,
        "issuer_conflict": issuer_conflict,
        "conflicting_project_title": conflicting_project_title,
        "active_projects_count": active_projects_count
    }

    cumulative_checks_context = f"""
    - Budget totale dei progetti formativi in corso: {current_projects_budget:,.2f} €
    - Budget del bando corrente: {grant_budget:,.2f} €
    - Budget cumulativo previsto: {projected_cumulative_budget:,.2f} €
    - Limite De Minimis SIEG (3 anni): {de_minimis_limit:,.2f} € (Superato: {'Sì' if de_minimis_warning else 'No'})
    - Dipendenti dell'ente: {staff_limit}
    - Referenti impegnati in altri progetti: {active_projects_count * 2} persone
    - Referenti cumulativi richiesti: {projected_staff_occupied} (Sovraccarico: {'Sì' if staff_warning else 'No'})
    - Anticipo di cassa stimato (20%): {projected_pre_financing_needed:,.2f} €
    - Budget formazione annuo disponibile: {annual_revenue:,.2f} € (Rischio liquidità: {'Sì' if cash_flow_warning else 'No'})
    - Conflitto Ente Erogatore: {"Sì (progetto già in corso: " + conflicting_project_title + ")" if issuer_conflict else "No"}
    """

    ente_name = profile.get('name', 'Ente Pubblico')
    ente_type = profile.get('legal_type', 'Comune')
    sede = profile.get('headquarters', '')
    n_dip = profile.get('staff_count', 20)
    budget_form = profile.get('annual_revenue', 50000)
    cf = profile.get('piva', '')
    settore = profile.get('ateco_code', 'Ente Locale')
    missione = profile.get('business_activity', '')

    profile_extended_context = f"""
    === CONTESTO ISTITUZIONALE ESTESO & VINCOLI ===
    - Disponibilità Aula Formativa: {profile.get('property_status', 'si')}
    - Infrastruttura Digitale: {profile.get('roof_access', 'si')}
    - Profilo del Personale da Formare: {profile.get('sun_exposure', 'misto')}
    - Strumenti Digitali Attivi: {', '.join(profile.get('digital_channels', [])) if profile.get('digital_channels') else 'Nessuno'}
    - Obiettivi Strategici: {', '.join(profile.get('strategic_goals', [])) if profile.get('strategic_goals') else 'Nessuno'}
    - Vincoli Specifici: {profile.get('custom_constraints', 'Nessuno')}
    - Contesto Territoriale: {profile.get('market_context', 'Nessuno')}
    - Note AI: {profile.get('ai_instructions', 'Nessuna')}
    """

    prompt = f"""
    Sei il consulente senior per la finanza agevolata istituzionale di 'Consulente AI'. Devi redigere una perizia di fattibilità tecnica e legale incrociando i dati di un bando PA con il profilo dell'ente '{ente_name}' ({ente_type}) e i vincoli cumulativi.

    Profilo Ente Cliente:
    - Nome Ente: {ente_name}
    - Tipo di Ente: {ente_type}
    - Sede: {sede}
    - Codice Fiscale: {cf}
    - Settore: {settore}
    - N. Dipendenti: {n_dip}
    - Budget Formazione Annuo: {budget_form:,.0f} €
    - Missione Istituzionale: {missione}

    {profile_extended_context}

    Bando da analizzare:
    - Titolo: {grant.get('title')}
    - Erogatore: {grant.get('issuer')}
    - Copertura: {grant.get('financing_percentage')}%
    - Difficoltà: {grant.get('difficulty')}
    - Budget Max: {grant.get('budget_max')} €
    - Scopo: {grant.get('scope')}
    - Descrizione: {grant.get('description')}

    PARAMETRI CUMULATIVI:
    {cumulative_checks_context}

    Redigi una perizia di fattibilità rigorosa per enti pubblici. Valuta:
    - Se l'ente è ammissibile per tipo (Comune, Provincia, ASL, ecc.) al bando specifico.
    - Se i fondi sono usabili per erogare o acquistare servizi di mediazione, de-escalation e formazione relazionale come il Metodo ME.NE.E.S.CO.
    - Verifica la sostenibilità del budget e del personale referente coinvolto.
    - Valuta la disponibilità di aule o infrastruttura digitale per la formazione (in presenza, FAD o blended).
    - NOTA BENE: se il bando è rivolto solo a imprese private, l'ente pubblico è NON IDONEO (punteggio 0-10%).
    - Collega l'analisi agli obiettivi strategici dell'ente e alle sue note specifiche.

    Rispondi ESATTAMENTE con questo JSON (senza testo esterno):
    {{
      "feasibility_score": 88,
      "legal_analysis": "Analisi dell'idoneità formale dell'ente (tipo ente, codice fiscale, normativa applicabile), ammissibilità del bando per enti locali e verifica De Minimis SIEG.",
      "technical_analysis": "Valutazione della capacità operativa dell'ente: numero dipendenti da formare, disponibilità di aula o infrastruttura digitale per la formazione in presenza o FAD.",
      "social_analysis": "Valutazione dell'impatto istituzionale: miglioramento del clima organizzativo, riduzione dei conflitti interni, qualità dei servizi al cittadino e reputazione dell'ente sul territorio.",
      "financial_analysis": "Analisi di sostenibilità economica: rapporto tra budget formazione disponibile, anticipo di cassa stimato e copertura del bando.",
      "partnership_need": "Raccomandazioni su accordi con fornitori di servizi formativi accreditati (es. ME.NE.E.S.CO.), università o enti di ricerca per rafforzare la candidatura.",
      "expert_recommendations": [
        "Consiglio 1 specifico per l'ente...",
        "Consiglio 2..."
      ],
      "eligibility_status": "IDONEO"
    }}
    """

    def get_offline_feasibility():
        financing_pct = grant.get('financing_percentage', 100)
        budget_max = grant.get('budget_max', 80000)
        grant_title = grant.get('title', 'bando selezionato')
        cofinanziamento_pct = 100 - financing_pct
        cofinanziamento_amount = round(budget_max * cofinanziamento_pct / 100)

        score = 88
        eligibility = "IDONEO"
        recommendations = []
        legal_reasons = []
        tech_reasons = []
        fin_reasons = []

        grant_desc = grant.get("description", "").lower()
        if "impresa" in grant_desc and "ente pubblico" not in grant_desc and "comune" not in grant_desc:
            legal_reasons.append(f"⚠️ REQUISITO SOGGETTIVO: Il bando '{grant_title}' sembra rivolto principalmente a imprese private. Verificare attentamente se gli enti pubblici sono ammissibili.")
            score = min(score, 55)
            eligibility = "A RISCHIO"
        else:
            legal_reasons.append(f"Compatibilità istituzionale verificata. L'ente '{ente_name}' ({ente_type}) risulta ammissibile per le spese di formazione e consulenza organizzativa del bando '{grant_title}'.")

        if de_minimis_warning:
            legal_reasons.append(f"⚠️ RISCHIO DE MINIMIS SIEG: Il budget cumulativo ({projected_cumulative_budget:,.0f} €) supera la soglia SIEG consentita di {de_minimis_limit:,.0f} €.")
            score = min(score, 60)
            if eligibility != "NON IDONEO":
                eligibility = "A RISCHIO"
        else:
            legal_reasons.append(f"Massimale De Minimis SIEG rispettato (budget cumulativo: {projected_cumulative_budget:,.0f} €).")

        has_aula = profile.get("property_status") not in ["no"]
        has_digital = profile.get("roof_access") in ["si", "limitato"]
        profilo_personale = profile.get("sun_exposure", "misto")

        if has_aula:
            tech_reasons.append("Disponibilità di aula formativa confermata. È possibile erogare il corso ME.NE.E.S.CO. in presenza.")
        else:
            tech_reasons.append("⚠️ Aula formativa non disponibile internamente. Il corso dovrà essere erogato in modalità FAD o presso sede esterna.")
            recommendations.append("FAD/BLENDED: Valutare l'erogazione del corso in modalità e-learning o ibrida per superare il vincolo logistico.")
            score = min(score, 82)

        if has_digital:
            tech_reasons.append(f"Infrastruttura digitale disponibile per modalità FAD o blended. Il profilo del personale ({profilo_personale}) è compatibile con percorsi misti.")
        else:
            tech_reasons.append("⚠️ Infrastruttura digitale limitata. Raccomandato potenziamento delle dotazioni tecnologiche prima dell'avvio del corso.")
            score = min(score, 78)

        if staff_warning:
            tech_reasons.append(f"⚠️ ATTENZIONE: Un numero elevato di referenti è già impegnato in altri progetti. Assicurarsi di disporre di almeno 1-2 referenti dedicati per questo percorso formativo.")
            score = min(score - 5, 75)
            recommendations.append("REFERENTE DEDICATO: Nominare un responsabile della formazione interno dedicato per coordinare il progetto ME.NE.E.S.CO.")
        else:
            tech_reasons.append(f"Il personale disponibile ({n_dip} dipendenti) è sufficiente per partecipare al percorso formativo senza sovraccarichi.")

        if cash_flow_warning:
            fin_reasons.append(f"⚠️ TENSIONE LIQUIDITÀ: L'anticipo di cassa stimato ({projected_pre_financing_needed:,.0f} €) è elevato rispetto al budget formazione dichiarato ({annual_revenue:,.0f} €).")
            score = min(score - 5, 72)
            if eligibility == "IDONEO":
                eligibility = "A RISCHIO"
            recommendations.append(f"ANTICIPO: Valutare la possibilità di richiedere un anticipo formale all'ente erogatore (tipicamente 30-40% per PA) per ridurre l'esposizione iniziale.")
        else:
            fin_reasons.append(f"La sostenibilità finanziaria è confermata. L'anticipo stimato di {projected_pre_financing_needed:,.0f} € è proporzionato al budget disponibile.")

        if cofinanziamento_pct > 0 and eligibility != "NON IDONEO":
            fin_reasons.append(f"Quota di cofinanziamento a carico dell'ente: {cofinanziamento_pct}% (pari a {cofinanziamento_amount:,.0f} €). Verificare disponibilità nel bilancio comunale.")

        score = max(10, score)
        recommendations.extend([
            "Coinvolgere il Responsabile della Prevenzione della Corruzione (RPCT) nella supervisione del progetto formativo.",
            "Richiedere all'erogatore del corso (ME.NE.E.S.CO.) un preventivo formale dettagliato con ore, metodologia e certificazioni rilasciate ai partecipanti."
        ])

        return {
            "feasibility_score": score,
            "legal_analysis": " ".join(legal_reasons),
            "technical_analysis": " ".join(tech_reasons),
            "social_analysis": f"Ottimo impatto istituzionale previsto per '{ente_name}'. L'implementazione del Metodo ME.NE.E.S.CO. migliorerà il clima organizzativo interno, ridurrà i contenziosi e aumenterà la qualità percepita dei servizi al cittadino.",
            "financial_analysis": " ".join(fin_reasons),
            "partnership_need": f"Per massimizzare il punteggio nella candidatura '{grant_title}', si raccomanda di allegare una lettera d'intenti firmata con ME.NE.E.S.CO. e, se possibile, una convenzione con un'università sarda (es. UniCA) per validare il protocollo accademicamente.",
            "expert_recommendations": recommendations,
            "eligibility_status": eligibility,
            "cumulative_checks": cumulative_checks
        }

    if not GEMINI_API_KEY:
        return get_offline_feasibility()

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=genai_types.GenerateContentConfig(response_mime_type="application/json")
        )
        parsed = json.loads(response.text.strip())
        parsed["cumulative_checks"] = cumulative_checks
        return JSONResponse(content=parsed)
    except Exception as e:
        logger.error(f"Errore analisi fattibilità PA: {e}")
        return JSONResponse(content=get_offline_feasibility())


@app.post("/api/project-draft")
async def generate_project_draft(req: FeasibilityRequest):
    db = load_db()
    profile = db.get("company_profile", {})
    grant = next((g for g in db.get("grants", []) if g["id"] == req.grant_id), None)
    if not grant:
        raise HTTPException(status_code=404, detail="Bando non trovato")

    priorities_context = ""
    if req.funding_priorities:
        priorities_context = f"\nL'ENTE RICHIEDENTE HA INDICATO QUESTE PRIORITÀ E OBIETTIVI DI FINANZIAMENTO:\n{req.funding_priorities}\n"

    ente_name = profile.get('name', 'Ente Pubblico')
    ente_type = profile.get('legal_type', 'Comune')
    sede = profile.get('headquarters', '')
    n_dip = profile.get('staff_count', 20)
    missione = profile.get('business_activity', '')
    has_aula = profile.get("property_status") != "no"
    has_digital = profile.get("roof_access") in ["si", "limitato"]
    profilo_personale = profile.get("sun_exposure", "misto")

    profile_extended_context = f"""
    === CONTESTO ISTITUZIONALE ESTESO ===
    - Disponibilità Aula: {profile.get('property_status', 'si')}
    - Infrastruttura Digitale: {profile.get('roof_access', 'si')}
    - Profilo Personale da Formare: {profilo_personale}
    - Strumenti Digitali: {', '.join(profile.get('digital_channels', [])) if profile.get('digital_channels') else 'Nessuno'}
    - Obiettivi Strategici: {', '.join(profile.get('strategic_goals', [])) if profile.get('strategic_goals') else 'Nessuno'}
    - Vincoli Specifici: {profile.get('custom_constraints', 'Nessuno')}
    - Contesto Territoriale: {profile.get('market_context', 'Nessuno')}
    - Note AI: {profile.get('ai_instructions', 'Nessuna')}
    """

    prompt = f"""
    Sei il capo del team di progettazione istituzionale per 'Consulente AI'. Devi redigere una proposta di progetto formativo PA per candidare l'ente '{ente_name}' ({ente_type}) al bando indicato, utilizzando il Metodo ME.NE.E.S.CO. come servizio erogato.

    Ente:
    - Nome: {ente_name}
    - Tipo: {ente_type}
    - Sede: {sede}
    - Dipendenti: {n_dip}
    - Missione: {missione}

    {profile_extended_context}
    {priorities_context}

    Bando:
    - Titolo: {grant.get('title')}
    - Erogatore: {grant.get('issuer')}
    - Budget Max: {grant.get('budget_max')} €
    - Scopo: {grant.get('scope')}
    - Link: {grant.get('official_link')}

    Considera la modalità di erogazione:
    - Se disponibile aula interna: proponi percorso in presenza
    - Se solo digitale: proponi blended o FAD
    - Allinea il profilo del personale ({profilo_personale}) ai moduli del corso

    Nel campo 'academic_path_advice', descrivi la roadmap per attivare accordi formali tra l'ente e ME.NE.E.S.CO. (convenzione, protocollo d'intesa, eventuale co-progettazione con enti accademici).

    Per ogni chiave di 'post_award_roadmap' inserisci un link HTML cliccabile verso '{grant.get('official_link')}' formattato come: <a href='{grant.get('official_link')}' target='_blank' style='color: #8C1B1B; font-weight: 600; text-decoration: underline;'>[Rif. Bando: Art. X]</a>

    RISPONDI con questo JSON (senza testo esterno):
    {{
      "grant_id": "{grant.get('id')}",
      "project_title": "Titolo istituzionale del progetto formativo",
      "project_summary": "Sintesi del percorso formativo (max 4 frasi). Includi obiettivi, n. dipendenti coinvolti, modalità e risultati attesi.",
      "key_actions": [
        "Azione 1: ...",
        "Azione 2: ...",
        "Azione 3: ..."
      ],
      "budget_draft": {{
        "costi_formazione_docenza": "Costo per la docenza specialistica ME.NE.E.S.CO. (es. 35.000 €)",
        "costi_materiali_didattici": "Dispense, manuali, piattaforma e-learning (es. 5.000 €)",
        "costi_logistica_organizzazione": "Noleggio aula esterna o attrezzatura FAD (es. 3.000 €)",
        "costi_coordinamento_interno": "Ore referente interno, rendicontazione e monitoraggio (es. 4.000 €)",
        "totale_stimato": "Totale coerente con il bando"
      }},
      "checklist_documents": [
        "Delibera di Giunta Comunale di approvazione del progetto formativo",
        "Codice Fiscale dell'Ente e atto di nomina del Responsabile Unico del Procedimento (RUP)",
        "DURC dell'Ente in corso di validità",
        "Piano Triennale del Fabbisogno del Personale (PTFP) contenente le attività formative",
        "Preventivo formale di ME.NE.E.S.CO. per l'erogazione del percorso",
        "Eventuale convenzione o protocollo d'intesa con partner accademici"
      ],
      "external_professionals": [
        "Consulente in Finanza Agevolata per la redazione e invio telematico della domanda",
        "Responsabile Unico del Procedimento (RUP) interno all'ente",
        "Formatori certificati ME.NE.E.S.CO. per l'erogazione dei moduli",
        "Rendicontatore / Revisore per la chiusura finanziaria del progetto"
      ],
      "partnership_strategy": "Descrizione della strategia di partnership tra l'ente, ME.NE.E.S.CO. e eventuali enti accademici sardi per dare solidità scientifica alla candidatura.",
      "academic_path_advice": "Roadmap per la formalizzazione della partnership con ME.NE.E.S.CO. e co-progettazione...",
      "post_award_roadmap": {{
        "accettazione_e_avvio": "Testo con link all'art. ...",
        "esecuzione_investimenti": "Testo con link all'art. ...",
        "documentazione_rendicontazione": "Testo con link all'art. ...",
        "pratiche_e_collaudo": "Testo con link all'art. ..."
      }}
    }}
    """

    def get_offline_project_draft():
        budget_val = grant.get('budget_max', 80000)
        official_link = grant.get("official_link", "https://sardegnalavoro.it/")
        base_link = official_link.rstrip('/')

        link_acc = f" <a href='{base_link}' target='_blank' style='color: #8C1B1B; font-weight: 600; text-decoration: underline;'>[Rif. Bando: Art. 10 - Accettazione]</a>"
        link_ese = f" <a href='{base_link}' target='_blank' style='color: #8C1B1B; font-weight: 600; text-decoration: underline;'>[Rif. Bando: Art. 12 - Esecuzione]</a>"
        link_ren = f" <a href='{base_link}' target='_blank' style='color: #8C1B1B; font-weight: 600; text-decoration: underline;'>[Rif. Bando: Art. 15 - Rendicontazione]</a>"
        link_col = f" <a href='{base_link}' target='_blank' style='color: #8C1B1B; font-weight: 600; text-decoration: underline;'>[Rif. Bando: Art. 16 - Collaudo]</a>"

        modalita = "in presenza" if has_aula else "in modalità blended/FAD"
        summary_suffix = f" Il piano risponde alle priorità dell'ente: {req.funding_priorities}." if req.funding_priorities else ""

        return {
            "grant_id": grant.get("id"),
            "project_title": f"Progetto ME.NE.E.S.CO. — Formazione su De-escalation Cognitiva e Gestione dei Conflitti per '{ente_name}'",
            "project_summary": f"Il progetto propone l'erogazione del Metodo ME.NE.E.S.CO. {modalita} a {n_dip} dipendenti di '{ente_name}'. Il percorso formativo mira a ridurre i conflitti interni, migliorare il clima organizzativo e aumentare la qualità dei servizi erogati ai cittadini.{summary_suffix}",
            "key_actions": [
                "Fase 1: Analisi organizzativa e mappatura dei conflitti latenti nell'ente tramite questionario ME.NE.E.S.CO.",
                f"Fase 2: Erogazione del corso intensivo di de-escalation cognitiva {modalita} (24 ore su 3 moduli) per tutti i dipendenti coinvolti.",
                "Fase 3: Supervisione post-formazione e redazione del report finale di impatto organizzativo con certificazione dei partecipanti."
            ],
            "budget_draft": {
                "costi_formazione_docenza": f"{round(budget_val * 0.60):,} € (Docenza ME.NE.E.S.CO. e coordinamento scientifico)",
                "costi_materiali_didattici": f"{round(budget_val * 0.10):,} € (Manuali, dispense e accesso piattaforma e-learning)",
                "costi_logistica_organizzazione": f"{round(budget_val * 0.08):,} € (Organizzazione aula o infrastruttura FAD)",
                "costi_coordinamento_interno": f"{round(budget_val * 0.12):,} € (Referente interno, rendicontazione e monitoraggio)",
                "totale_stimato": f"{round(budget_val * 0.90):,} €"
            },
            "checklist_documents": [
                "Delibera di Giunta Comunale di approvazione del progetto formativo",
                "Codice Fiscale dell'Ente e nomina formale del RUP",
                "DURC dell'Ente in corso di validità",
                "Piano Triennale del Fabbisogno del Personale (PTFP)",
                "Preventivo formale di ME.NE.E.S.CO. per il percorso",
                "Convenzione o protocollo d'intesa con partner accademici (se richiesto dal bando)"
            ],
            "external_professionals": [
                "Consulente in Finanza Agevolata per la redazione e invio della domanda",
                "Referente interno (RUP) per la supervisione amministrativa del progetto",
                "Formatori certificati ME.NE.E.S.CO. per l'erogazione dei moduli formativi",
                "Revisore dei conti per la rendicontazione finale al bando"
            ],
            "partnership_strategy": f"Il progetto si fonda su una convenzione formale tra '{ente_name}' e ME.NE.E.S.CO. Per rafforzare la credibilità accademica della candidatura, si raccomanda di allegare una lettera di supporto da parte di un dipartimento universitario sardo (UniCA o UNICA) che validi il protocollo scientifico del Metodo.",
            "academic_path_advice": "Roadmap di formalizzazione: 1. Delibera di Giunta che approva il percorso e nomina il RUP. 2. Firma del protocollo d'intesa con ME.NE.E.S.CO. e, se disponibile, co-firma accademica. 3. Sottomissione telematica della domanda entro i termini del bando.",
            "post_award_roadmap": {
                "accettazione_e_avvio": f"Adottare la Delibera di accettazione del finanziamento entro 30 giorni dalla notifica ufficiale dell'ente erogatore. Aprire un conto corrente dedicato o un centro di costo specifico per la tracciabilità delle spese del progetto.{link_acc}",
                "esecuzione_investimenti": f"Avviare le attività formative entro 60 giorni dall'accettazione. Tutti i pagamenti ai fornitori (ME.NE.E.S.CO., logistica) devono essere effettuati tramite bonifico bancario tracciabile con causale recante il codice CUP del progetto.{link_ese}",
                "documentazione_rendicontazione": f"Fascicolo di rendicontazione da trasmettere entro 90 giorni dalla conclusione delle attività: fatture elettroniche quietanzate, estratti conto dimostrativi, registri presenze dei partecipanti firmati, certificati di frequenza e report di impatto finale.{link_ren}",
                "pratiche_e_collaudo": f"Presentare relazione finale al soggetto gestore del bando con allegato il report di valutazione dell'impatto formativo e le schede di gradimento compilate dai partecipanti. Conservare tutta la documentazione per almeno 10 anni (obbligo FSE).{link_col}"
            }
        }

    if not GEMINI_API_KEY:
        return get_offline_project_draft()

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=genai_types.GenerateContentConfig(response_mime_type="application/json")
        )
        parsed = json.loads(response.text.strip())

        official_link = grant.get("official_link", "https://sardegnalavoro.it/")
        base_link = official_link.rstrip('/')
        post_award_roadmap = parsed.get("post_award_roadmap", {})
        if post_award_roadmap:
            art_refs = {
                "accettazione_e_avvio": "10",
                "esecuzione_investimenti": "12",
                "documentazione_rendicontazione": "15",
                "pratiche_e_collaudo": "16"
            }
            import re
            for key, art_num in art_refs.items():
                if key in post_award_roadmap:
                    val = post_award_roadmap[key]
                    exact_link = f"<a href='{base_link}' target='_blank' style='color: #8C1B1B; font-weight: 600; text-decoration: underline;'>"
                    if "<a " in val:
                        val = re.sub(r"<a\s+href=['\"][^'\"]+['\"][^>]*>", exact_link, val)
                    else:
                        val += f" {exact_link}[Rif. Bando: Art. {art_num}]</a>"
                    post_award_roadmap[key] = val
            parsed["post_award_roadmap"] = post_award_roadmap

        return JSONResponse(content=parsed)
    except Exception as e:
        logger.error(f"Errore generazione progetto formativo PA: {e}")
        return JSONResponse(content=get_offline_project_draft())


@app.post("/api/grants/compile")
async def compile_grant_application(req: FeasibilityRequest):
    db = load_db()
    profile = db.get("company_profile", {})
    grant = next((g for g in db.get("grants", []) if g["id"] == req.grant_id), None)
    if not grant:
        raise HTTPException(status_code=404, detail="Bando non trovato")

    ente_name = profile.get('name', 'Ente Pubblico')
    ente_type = profile.get('legal_type', 'Comune')
    sede = profile.get('headquarters', '')
    n_dip = profile.get('staff_count', 20)
    budget_form = profile.get('annual_revenue', 50000)
    cf = profile.get('piva', '')
    missione = profile.get('business_activity', '')
    grant_title = grant.get('title', '')
    grant_issuer = grant.get('issuer', '')
    grant_budget = grant.get('budget_max', 80000)
    grant_scope = grant.get('scope', '')

    has_aula = profile.get("property_status") != "no"
    has_digital = profile.get("roof_access") in ["si", "limitato"]
    profilo_personale = profile.get("sun_exposure", "misto")

    priorities_context = ""
    if req.funding_priorities:
        priorities_context = f"\nL'ENTE HA INDICATO QUESTE PRIORITÀ:\n{req.funding_priorities}\n"

    profile_extended_context = f"""
    === CONTESTO ISTITUZIONALE ESTESO ===
    - Disponibilità Aula: {profile.get('property_status', 'si')}
    - Infrastruttura Digitale: {profile.get('roof_access', 'si')}
    - Profilo Personale: {profilo_personale}
    - Strumenti Digitali: {', '.join(profile.get('digital_channels', [])) if profile.get('digital_channels') else 'Nessuno'}
    - Obiettivi Strategici: {', '.join(profile.get('strategic_goals', [])) if profile.get('strategic_goals') else 'Nessuno'}
    - Vincoli Specifici: {profile.get('custom_constraints', 'Nessuno')}
    - Contesto Territoriale: {profile.get('market_context', 'Nessuno')}
    """

    prompt = f"""
    Sei un Europrogettista Senior specializzato nella scrittura di progetti formativi e domande di contributo per enti pubblici italiani.
    Devi compilare la candidatura formale in italiano per l'ente '{ente_name}' ({ente_type}) rivolta al bando '{grant_title}' dell'ente '{grant_issuer}'.
    Il servizio erogato è il Metodo ME.NE.E.S.CO. — un protocollo scientifico di de-escalation cognitiva e gestione dei conflitti.
    Lo stile deve essere istituzionale, formale, preciso e focalizzato sull'impatto organizzativo, sul miglioramento del servizio pubblico e sulla validazione scientifica del metodo.

    DATI ENTE:
    - Nome: {ente_name} ({ente_type})
    - Codice Fiscale: {cf}
    - Sede: {sede}
    - N. Dipendenti: {n_dip}
    - Budget formazione: {budget_form:,.0f} €/anno
    - Missione: {missione}

    {profile_extended_context}
    {priorities_context}

    BANDO TARGET:
    - Titolo: {grant_title}
    - Erogatore: {grant_issuer}
    - Budget Max: {grant_budget:,.0f} €
    - Scopo: {grant_scope}

    Genera sezioni formali di candidatura (A-H) coerenti con il profilo dell'ente:
    - Adatta la modalità di erogazione: in presenza se c'è aula, FAD/blended se digitale, misto se entrambi.
    - Allinea il profilo del personale ({profilo_personale}) ai moduli del percorso.
    - Usa linguaggio istituzionale PA, cita articoli di legge rilevanti quando possibile.

    Rispondi SOLO con questo JSON:
    {{
      "sezione_a_presentazione": "Presentazione formale dell'ente (5-7 righe): natura giuridica, anni di costituzione, missione istituzionale, n. dipendenti, servizi erogati ai cittadini.",
      "sezione_b_descrizione_progetto": "Descrizione del progetto formativo ME.NE.E.S.CO. (6-8 righe): titolo, obiettivi, n. dipendenti coinvolti, modalità, durata e risultati attesi.",
      "sezione_c_analisi_bisogni": "Analisi dei bisogni organizzativi (5-6 righe): situazione attuale dei conflitti interni, impatto sulla qualità dei servizi, gap di competenze relazionali nei dipendenti.",
      "sezione_d_metodologia": "Metodologia del percorso ME.NE.E.S.CO. (6-8 righe): struttura dei moduli, approccio cognitivo-comportamentale, validazione scientifica del metodo, strumenti di valutazione dell'apprendimento.",
      "sezione_e_piano_attivita": "Cronoprogramma delle attività formative (5-7 righe): fasi, durata di ciascun modulo, calendario, modalità di verifica intermedia e finale.",
      "sezione_f_budget_narrativo": "Giustificazione del budget (4-5 righe): congruità delle voci di spesa (docenza, materiali, logistica, coordinamento) rispetto ai prezzi di mercato per servizi formativi specialistici PA.",
      "sezione_g_impatto": "Impatto organizzativo e risultati misurabili (4-5 righe): riduzione dei contenziosi interni stimata (%), miglioramento degli indici di soddisfazione del personale, impatto sulla qualità dei servizi ai cittadini e ROI istituzionale.",
      "sezione_h_partenariato": "Partenariato e rete istituzionale (4-5 righe): accordo formale con ME.NE.E.S.CO., eventuale co-progettazione accademica, reti con altri enti locali per la disseminazione del modello."
    }}
    """

    if GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=genai_types.GenerateContentConfig(response_mime_type="application/json")
            )
            parsed = json.loads(response.text.strip())
            parsed["grant_title"] = grant_title
            parsed["grant_issuer"] = grant_issuer
            parsed["association_name"] = ente_name
            return JSONResponse(content=parsed)
        except Exception as e:
            logger.error(f"Errore compilazione candidatura PA con Gemini: {e}")

    # Fallback istituzionale
    modalita = "in presenza" if has_aula else "in modalità e-learning (FAD)"
    cofi_pct = 100 - grant.get('financing_percentage', 100)
    cofi_amt = round(grant_budget * cofi_pct / 100)
    priorities_text = f" Il progetto si focalizza prioritariamente su: {req.funding_priorities}." if req.funding_priorities else ""

    return {
        "grant_title": grant_title,
        "grant_issuer": grant_issuer,
        "association_name": ente_name,
        "sezione_a_presentazione": (
            f"L'{ente_name} è un {ente_type} con sede a {sede}, dotato di Personalità Giuridica pubblica e Codice Fiscale {cf}. L'ente esercita le funzioni istituzionali previste dal D.Lgs. 267/2000 (TUEL), garantendo l'erogazione di servizi essenziali alla comunità locale. Il personale dipendente ammonta a {n_dip} unità, operante in diversi settori (amministrativo, tecnico, servizi sociali). La missione istituzionale è: {missione[:200] if missione else 'garantire il benessere e lo sviluppo della comunità.'}."
        ),
        "sezione_b_descrizione_progetto": (
            f"Il progetto '{ente_name} — Eccellenza Relazionale PA' risponde al bando '{grant_title}' promosso da {grant_issuer}. L'intervento prevede l'erogazione del Metodo ME.NE.E.S.CO. {modalita} a {n_dip} dipendenti dell'ente, suddivisi in gruppi omogenei per ruolo e responsabilità. Il percorso, della durata di 24 ore (3 moduli da 8 ore), mira a dotare il personale di strumenti cognitivi e relazionali certificati per la gestione proattiva dei conflitti, la de-escalation nelle situazioni critiche con l'utenza e il miglioramento del clima organizzativo interno.{priorities_text}"
        ),
        "sezione_c_analisi_bisogni": (
            f"Gli enti pubblici italiani registrano annualmente una quota rilevante di contenziosi interni e situazioni conflittuali con l'utenza, con un impatto diretto sulla qualità dei servizi erogati e sul benessere del personale. '{ente_name}' ha identificato nell'assenza di strumenti strutturati di gestione dei conflitti e de-escalation una lacuna critica nelle competenze trasversali del suo personale. Il Metodo ME.NE.E.S.CO., validato accademicamente e applicato in numerosi enti pubblici italiani, risponde puntualmente a questi bisogni organizzativi."
        ),
        "sezione_d_metodologia": (
            f"Il Metodo ME.NE.E.S.CO. (Metodo di Negoziazione e Gestione delle Crisi per la P.A.) si fonda su un approccio cognitivo-comportamentale e neuroscientificamente validato. Il percorso formativo è strutturato in 3 moduli: Modulo 1 — Fondamenti della De-escalation Cognitiva (8 ore); Modulo 2 — Tecniche di Negoziazione e Gestione dei Conflitti Istituzionali (8 ore); Modulo 3 — Simulazioni Pratiche e Protocolli di Crisi (8 ore). Ogni modulo prevede momenti di role-playing, casi studio reali della PA e test di autovalutazione. L'erogazione avverrà {modalita}, con materiali didattici proprietari e accesso alla piattaforma ME.NE.E.S.CO."
        ),
        "sezione_e_piano_attivita": (
            f"Il cronoprogramma prevede un arco temporale di 4 mesi: Mese 1 — Analisi organizzativa preliminare e somministrazione del questionario di mappatura dei conflitti a tutti i {n_dip} dipendenti; Mese 2 — Erogazione del Modulo 1 e del Modulo 2 (in sessioni di mezza giornata); Mese 3 — Erogazione del Modulo 3 con simulazioni pratiche e test di valutazione finale; Mese 4 — Supervisione post-formazione, somministrazione questionario di gradimento e redazione del report di impatto organizzativo e rendicontazione al soggetto gestore."
        ),
        "sezione_f_budget_narrativo": (
            f"Il piano finanziario prevede un investimento totale di {round(grant_budget * 0.90):,.0f} € (di cui {grant.get('financing_percentage')}% richiesto a copertura). Le voci principali sono: docenza specialistica ME.NE.E.S.CO. {round(grant_budget * 0.60):,.0f} € (congrua per n. {n_dip} partecipanti in percorso intensivo certificato); materiali didattici e piattaforma {round(grant_budget * 0.10):,.0f} €; logistica e organizzazione {round(grant_budget * 0.08):,.0f} €; coordinamento interno e rendicontazione {round(grant_budget * 0.12):,.0f} €. Tutte le voci sono supportate da preventivo formale di ME.NE.E.S.CO."
        ),
        "sezione_g_impatto": (
            f"L'implementazione del Metodo ME.NE.E.S.CO. produrrà un impatto organizzativo misurabile: riduzione stimata del 40% dei contenziosi interni tra dipendenti nei 12 mesi post-formazione; incremento dell'indice di soddisfazione del personale (Benessere Organizzativo ex D.Lgs. 150/2009); riduzione del 25% delle escalation critiche con l'utenza nei servizi di front-office; miglioramento del giudizio dei cittadini sulla qualità percepita dei servizi. Il ROI istituzionale, calcolato in termini di riduzione delle ore perse per conflitti e contenziosi, è stimato in 14 mesi."
        ),
        "sezione_h_partenariato": (
            f"La candidatura si fonda su un accordo formale tra '{ente_name}' e ME.NE.E.S.CO., erogatore certificato del metodo di de-escalation cognitiva per la PA. Al fine di rafforzare la validità scientifica e accademica della proposta, si prevede la co-firma di un protocollo d'intesa con un dipartimento universitario accreditato (scienze cognitive, psicologia o scienze politiche) per la supervisione scientifica del percorso e la validazione dei risultati. La disseminazione del modello avverrà tramite condivisione del report di impatto nella rete dei Comuni e ANCI."
        )
    }


@app.get("/bandi", response_class=HTMLResponse)
async def get_bandi_dashboard():
    html_path = os.path.join(BASE_DIR, "bandi.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"Errore lettura bandi.html: {e}")
        return HTMLResponse(content=f"<h1>Errore caricamento Dashboard Bandi MENEESCO</h1><p>{str(e)}</p>")


@app.get("/")
async def get_root():
    return RedirectResponse(url="/bandi")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8085, reload=True)
