import os
import json
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

app = FastAPI(
    title="Il Campanellino Server",
    description="Server di backend per la landing page di Il Campanellino - Eventi e Spettacolo.",
    version="1.0.0"
)

# File database per registrare i contatti e le visite dei clienti
LEADS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.json")
VISITS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "visite.json")

# Inizializza file dei leads se non esiste
if not os.path.exists(LEADS_FILE):
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=4)

# Inizializza file delle visite se non esiste
if not os.path.exists(VISITS_FILE):
    with open(VISITS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=4)

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="File index.html non trovato.")
    
    with open(index_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return html_content

@app.post("/api/visita")
async def save_visit(request: Request):
    try:
        data = await request.json()
        variante = data.get("variante", "A")
        
        nuova_visita = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "variante": variante
        }
        
        visite = []
        if os.path.exists(VISITS_FILE):
            with open(VISITS_FILE, "r", encoding="utf-8") as f:
                try:
                    visite = json.load(f)
                except json.JSONDecodeError:
                    visite = []
                    
        visite.append(nuova_visita)
        
        with open(VISITS_FILE, "w", encoding="utf-8") as f:
            json.dump(visite, f, ensure_ascii=False, indent=4)
            
        return {"success": True, "message": "Visita registrata."}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Errore interno: {str(e)}"}
        )

@app.post("/api/contatto")
async def save_lead(request: Request):
    try:
        data = await request.json()
        nome = data.get("nome")
        tipo_cliente = data.get("tipo_cliente")  # Azienda, Ente Pubblico, Privato
        email = data.get("email")
        tipo_evento = data.get("tipo_evento")  # Musical, Laboratorio, Matrimonio, Spot, Flash-mob
        telefono = data.get("telefono", "")
        dettagli = data.get("dettagli", "")
        variante_ab = data.get("variante_ab", "A")

        if not all([nome, tipo_cliente, email, tipo_evento]):
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Tutti i campi contrassegnati con asterisco sono obbligatori."}
            )

        new_lead = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "data_registrazione": datetime.now().strftime("%d/%m/%Y alle ore %H:%M:%S"),
            "nome": nome,
            "tipo_cliente": tipo_cliente,
            "email": email,
            "tipo_evento": tipo_evento,
            "telefono": telefono,
            "dettagli": dettagli,
            "variante_ab": variante_ab,
            "stato": "Nuova Richiesta"
        }

        # Leggi ed aggiorna database locale dei leads
        leads = []
        if os.path.exists(LEADS_FILE):
            with open(LEADS_FILE, "r", encoding="utf-8") as f:
                try:
                    leads = json.load(f)
                except json.JSONDecodeError:
                    leads = []

        leads.append(new_lead)

        with open(LEADS_FILE, "w", encoding="utf-8") as f:
            json.dump(leads, f, ensure_ascii=False, indent=4)

        return {"success": True, "message": "Contatto salvato con successo."}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Errore interno del server: {str(e)}"}
        )

@app.get("/api/statistiche")
async def get_stats():
    try:
        # Carica visite
        visite = []
        if os.path.exists(VISITS_FILE):
            with open(VISITS_FILE, "r", encoding="utf-8") as f:
                try:
                    visite = json.load(f)
                except json.JSONDecodeError:
                    visite = []
                    
        # Carica leads
        leads = []
        if os.path.exists(LEADS_FILE):
            with open(LEADS_FILE, "r", encoding="utf-8") as f:
                try:
                    leads = json.load(f)
                except json.JSONDecodeError:
                    leads = []
                    
        # Conteggi
        visite_a = sum(1 for v in visite if v.get("variante") == "A")
        visite_b = sum(1 for v in visite if v.get("variante") == "B")
        
        leads_a = sum(1 for l in leads if l.get("variante_ab") == "A")
        leads_b = sum(1 for l in leads if l.get("variante_ab") == "B")
        
        cr_a = (leads_a / visite_a * 100) if visite_a > 0 else 0.0
        cr_b = (leads_b / visite_b * 100) if visite_b > 0 else 0.0
        
        return {
            "success": True,
            "statistiche": {
                "Variante A (Controllo)": {
                    "visite": visite_a,
                    "leads": leads_a,
                    "conversion_rate": round(cr_a, 2)
                },
                "Variante B (Rassicurazione)": {
                    "visite": visite_b,
                    "leads": leads_b,
                    "conversion_rate": round(cr_b, 2)
                }
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )

@app.get("/stats", response_class=HTMLResponse)
async def get_stats_page():
    # Calcola statistiche in-line
    visite = []
    if os.path.exists(VISITS_FILE):
        with open(VISITS_FILE, "r", encoding="utf-8") as f:
            try: visite = json.load(f)
            except: visite = []
    leads = []
    if os.path.exists(LEADS_FILE):
        with open(LEADS_FILE, "r", encoding="utf-8") as f:
            try: leads = json.load(f)
            except: leads = []
            
    visite_a = sum(1 for v in visite if v.get("variante") == "A")
    visite_b = sum(1 for v in visite if v.get("variante") == "B")
    leads_a = sum(1 for l in leads if l.get("variante_ab") == "A")
    leads_b = sum(1 for l in leads if l.get("variante_ab") == "B")
    
    cr_a = (leads_a / visite_a * 100) if visite_a > 0 else 0.0
    cr_b = (leads_b / visite_b * 100) if visite_b > 0 else 0.0
    
    # Costruiamo la tabella per gli ultimi 10 leads ricevuti
    leads_rows = ""
    if leads:
        for l in reversed(leads[-10:]):
            leads_rows += f"""<tr>
                <td>{l.get("data_registrazione", "").replace(" alle ore", "")}</td>
                <td>{l.get("nome")}</td>
                <td>{l.get("email")}</td>
                <td>{l.get("tipo_evento")}</td>
                <td><span class="badge {l.get("variante_ab", "A").lower()}">Variante {l.get("variante_ab", "A")}</span></td>
                <td>{l.get("stato")}</td>
            </tr>"""
    else:
        leads_rows = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">Nessun lead ricevuto per ora.</td></tr>'
        
    html_content = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Statistiche A/B Testing — Il Campanellino</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #070512;
            --bg-secondary: #130E29;
            --brand-primary: #FFA800;
            --brand-secondary: #EC4899;
            --text-main: #F3F4F6;
            --text-muted: #A1A1AA;
            --border-color: rgba(255, 168, 0, 0.15);
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-main);
            padding: 40px 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 2rem;
            margin-bottom: 30px;
            color: #ffffff;
            border-bottom: 2px solid var(--brand-primary);
            padding-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .card {{
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);
            position: relative;
            overflow: hidden;
        }}
        .card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; width: 4px; height: 100%;
        }}
        .card.variant-a::before {{ background-color: var(--brand-secondary); }}
        .card.variant-b::before {{ background-color: var(--brand-primary); }}
        .card-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.3rem;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
        }}
        .metric-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 12px;
            padding-bottom: 12px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        .metric-row:last-child {{
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }}
        .metric-label {{ color: var(--text-muted); }}
        .metric-val {{ font-weight: 600; font-size: 1.1rem; }}
        .cr-val {{
            font-size: 1.8rem;
            color: #ffffff;
            font-weight: 700;
        }}
        .back-btn {{
            display: inline-block;
            background: transparent;
            color: var(--text-muted);
            border: 1px solid var(--text-muted);
            padding: 8px 16px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 0.9rem;
            transition: all 0.3s;
        }}
        .back-btn:hover {{
            color: #fff;
            border-color: #fff;
            background: rgba(255,255,255,0.05);
        }}
        .leads-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 0.9rem;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
        }}
        .leads-table th, .leads-table td {{
            padding: 12px 15px;
            text-align: left;
        }}
        .leads-table th {{
            background: rgba(255, 168, 0, 0.1);
            color: var(--brand-primary);
            font-family: 'Outfit', sans-serif;
        }}
        .leads-table tr {{
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}
        .leads-table tr:last-child {{
            border-bottom: none;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .badge.a {{ background: rgba(236, 72, 153, 0.15); color: var(--brand-secondary); }}
        .badge.b {{ background: rgba(255, 168, 0, 0.15); color: var(--brand-primary); }}
    </style>
</head>
<body>
    <div class="container">
        <h1>
            <span>Dashboard Test A/B locale</span>
            <a href="/" class="back-btn">← Torna al Sito</a>
        </h1>
        
        <div class="grid">
            <div class="card variant-a">
                <div class="card-title">
                    <span>Variante A</span>
                    <span style="color: var(--brand-secondary)">Controllo</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Visite (Sessioni)</span>
                    <span class="metric-val">{visite_a}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Contatti Ricevuti (Leads)</span>
                    <span class="metric-val">{leads_a}</span>
                </div>
                <div class="metric-row" style="align-items: center;">
                    <span class="metric-label">Tasso Conversione (CR)</span>
                    <span class="cr-val">{cr_a:.2f}%</span>
                </div>
            </div>
            
            <div class="card variant-b">
                <div class="card-title">
                    <span>Variante B</span>
                    <span style="color: var(--brand-primary)">Sfidante / Rassicurazione</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Visite (Sessioni)</span>
                    <span class="metric-val">{visite_b}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Contatti Ricevuti (Leads)</span>
                    <span class="metric-val">{leads_b}</span>
                </div>
                <div class="metric-row" style="align-items: center;">
                    <span class="metric-label">Tasso Conversione (CR)</span>
                    <span class="cr-val" style="color: var(--brand-primary);">{cr_b:.2f}%</span>
                </div>
            </div>
        </div>
        
        <h2 style="font-family: Outfit; font-size: 1.5rem; margin-bottom: 15px;">Ultimi Leads Ricevuti (Locale)</h2>
        <table class="leads-table">
            <thead>
                <tr>
                    <th>Data</th>
                    <th>Nome</th>
                    <th>Email</th>
                    <th>Evento</th>
                    <th>Variante</th>
                    <th>Stato</th>
                </tr>
            </thead>
            <tbody>
                {leads_rows}
            </tbody>
        </table>
    </div>
</body>
</html>"""
    return html_content

if __name__ == "__main__":
    print("Il Campanellino Server attivo su http://127.0.0.1:8085")
    uvicorn.run("app:app", host="127.0.0.1", port=8085, reload=True)
