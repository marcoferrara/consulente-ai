import os
import json
from datetime import datetime
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI(
    title="Meneesco Landing Page Server",
    description="Server di backend per la landing page di presentazione istituzionale del Metodo Meneesco.",
    version="1.0.0"
)

# File database per registrare le richieste istituzionali ricevute
LEADS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.json")

# Inizializza file dei leads se non esiste
if not os.path.exists(LEADS_FILE):
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=4)

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="File index.html non trovato.")
    
    with open(index_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return html_content

@app.get("/47120255_padded_logo.png")
async def get_logo():
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "47120255_padded_logo.png")
    if not os.path.exists(logo_path):
        raise HTTPException(status_code=404, detail="Logo non trovato.")
    return FileResponse(logo_path)

@app.get("/favicon.ico")
async def get_favicon():
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "47120255_padded_logo.png")
    if not os.path.exists(logo_path):
        raise HTTPException(status_code=404, detail="Logo non trovato per favicon.")
    return FileResponse(logo_path)

@app.post("/api/richiesta")
async def save_lead(request: Request):
    try:
        data = await request.json()
        nome = data.get("nome")
        ruolo = data.get("ruolo")
        ente = data.get("ente")
        email = data.get("email")
        abitanti = data.get("abitanti")
        messaggio = data.get("messaggio", "")

        if not all([nome, ruolo, ente, email, abitanti]):
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Tutti i campi contrassegnati con asterisco sono obbligatori."}
            )

        new_lead = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "data_registrazione": datetime.now().strftime("%d/%m/%Y alle ore %H:%M:%S"),
            "nome": nome,
            "ruolo": ruolo,
            "ente": ente,
            "email": email,
            "abitanti": abitanti,
            "messaggio": messaggio,
            "stato": "In Attesa di Contatto"
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

        return {"success": True, "message": "Richiesta istituzionale salvata con successo."}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Errore interno del server: {str(e)}"}
        )

if __name__ == "__main__":
    print("Meneesco Landing Page Server attivo su http://127.0.0.1:8084")
    uvicorn.run("app:app", host="127.0.0.1", port=8084, reload=True)
