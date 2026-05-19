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

# File database per registrare i contatti dei clienti
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

@app.post("/api/contatto")
async def save_lead(request: Request):
    try:
        data = await request.json()
        nome = data.get("nome")
        tipo_cliente = data.get("tipo_cliente")  # Azienda, Ente Pubblico, Privato
        email = data.get("email")
        tipo_evento = data.get("tipo_evento")  # Musical, Laboratorio, Matrimonio, Spot, Flash-mob
        dettagli = data.get("dettagli", "")

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
            "dettagli": dettagli,
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

if __name__ == "__main__":
    print("Il Campanellino Server attivo su http://127.0.0.1:8085")
    uvicorn.run("app:app", host="127.0.0.1", port=8085, reload=True)
