import os
import json
import logging
import random
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import google.generativeai as genai
import dotenv

# Load environment variables
dotenv.load_dotenv(dotenv_path="../.env")
dotenv.load_dotenv()  # also check local folder

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("social_media_automation")

app = FastAPI(title="Antiga Armonia — Instagram SMM Automation Simulation")

# Database Path (supporta directory persistente per ambienti cloud)
PERSISTENT_DATA_DIR = os.getenv("PERSISTENT_DATA_DIR")
if PERSISTENT_DATA_DIR:
    PERSISTENT_DATA_DIR = os.path.abspath(PERSISTENT_DATA_DIR)
    os.makedirs(PERSISTENT_DATA_DIR, exist_ok=True)
    DB_PATH = os.path.join(PERSISTENT_DATA_DIR, "social_database.json")
    default_db = os.path.join(os.path.dirname(__file__), "database.json")
    if not os.path.exists(DB_PATH) and os.path.exists(default_db):
        try:
            import shutil
            shutil.copy2(default_db, DB_PATH)
            logger.info(f"Copiato database social di default in {DB_PATH}")
        except Exception as e:
            logger.error(f"Errore copia database social di default: {e}")
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), "database.json")


# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
gemini_active = False

if api_key:
    try:
        genai.configure(api_key=api_key)
        # Test model availability
        model = genai.GenerativeModel("gemini-2.5-flash")
        gemini_active = True
        logger.info("Gemini API configurata con successo per Instagram Automation.")
    except Exception as e:
        logger.error(f"Errore nella configurazione di Gemini API: {e}")
else:
    logger.warning("GEMINI_API_KEY non trovata. Verrà utilizzata la simulazione locale dei post.")

def read_db():
    if not os.path.exists(DB_PATH):
        return {"posts": [], "unread_directives": []}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def write_db(data):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Serve templates
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(TEMPLATES_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Frontend non trovato. Esegui il build.")

# API ENDPOINTS
@app.get("/api/posts")
async def get_posts():
    db = read_db()
    return {
        "posts": db.get("posts", []),
        "unread_directives": db.get("unread_directives", [])
    }

@app.post("/api/posts")
async def add_post(post: dict = Body(...)):
    db = read_db()
    new_id = f"post_{len(db['posts']) + 1:03d}"
    post["id"] = new_id
    post["published_date"] = None
    post["engagement"] = None
    db["posts"].append(post)
    write_db(db)
    return {"status": "success", "post": post}

@app.post("/api/posts/edit/{post_id}")
async def edit_post(post_id: str, payload: dict = Body(...)):
    db = read_db()
    post = next((p for p in db["posts"] if p["id"] == post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post non trovato")
    
    post["type"] = payload.get("type", post["type"])
    post["generated_copy"] = payload.get("generated_copy", post["generated_copy"])
    post["hashtags"] = payload.get("hashtags", post["hashtags"])
    post["scheduled_time"] = payload.get("scheduled_time", post["scheduled_time"])
    post["status"] = payload.get("status", post["status"])
    
    write_db(db)
    return {"status": "success", "post": post}

@app.delete("/api/posts/{post_id}")
async def delete_post(post_id: str):
    db = read_db()
    db["posts"] = [p for p in db["posts"] if p["id"] != post_id]
    write_db(db)
    return {"status": "success", "message": "Post eliminato"}

@app.post("/api/posts/{post_id}/approve")
async def approve_post(post_id: str, payload: dict = Body(...)):
    db = read_db()
    post = next((p for p in db["posts"] if p["id"] == post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post non trovato")
    
    post["status"] = "Approvato"
    post["scheduled_time"] = payload.get("scheduled_time", post["scheduled_time"])
    write_db(db)
    return {"status": "success", "post": post}

@app.post("/api/posts/{post_id}/publish")
async def publish_post(post_id: str):
    db = read_db()
    post = next((p for p in db["posts"] if p["id"] == post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post non trovato")
    
    post["status"] = "Pubblicato"
    post["published_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Generate high-fidelity simulation statistics based on type
    is_reel = post["type"].lower() == "reels"
    likes = random.randint(300, 600) if is_reel else random.randint(120, 280)
    comments = random.randint(40, 95) if is_reel else random.randint(10, 35)
    shares = random.randint(50, 150) if is_reel else random.randint(5, 25)
    saves = random.randint(20, 70) if is_reel else random.randint(10, 40)
    reach = random.randint(2500, 5800) if is_reel else random.randint(900, 1900)
    
    post["engagement"] = {
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "saves": saves,
        "reach": reach
    }
    
    write_db(db)
    return {"status": "success", "post": post}

@app.post("/api/posts/generate")
async def generate_post_api(payload: dict = Body(...)):
    directive = payload.get("original_directive", "").strip()
    media_path = payload.get("media_path", "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=800&q=80")
    post_type = payload.get("type", "Post")
    
    if not directive:
        raise HTTPException(status_code=400, detail="Direttiva vuota")
        
    generated = await generate_ai_post(directive, post_type)
    
    return {
        "status": "success",
        "post": {
            "type": post_type,
            "original_directive": directive,
            "media_path": media_path,
            "generated_copy": generated["copy"],
            "hashtags": generated["hashtags"],
            "suggested_time": generated["suggested_time"],
            "scheduled_time": datetime.now().strftime("%Y-%m-%d") + " " + generated["suggested_time"],
            "status": "In Attesa di Approvazione",
            "source": "Manuale Dashboard"
        }
    }

@app.post("/api/inbox/sync")
async def sync_inbox():
    db = read_db()
    unread = db.get("unread_directives", [])
    
    if not unread:
        return {
            "status": "success",
            "count": 0,
            "message": "Nessuna nuova email o messaggio WhatsApp da elaborare nella casella della direzione."
        }
        
    count = 0
    new_posts = []
    
    for d in unread:
        # Determine type
        p_type = "Reels" if "reel" in d["text"].lower() or "video" in d["text"].lower() else "Post"
        
        # Generate with Gemini or mock
        generated = await generate_ai_post(d["text"], p_type)
        
        # Create Post object
        new_id = f"post_{len(db['posts']) + 1:03d}"
        new_post = {
            "id": new_id,
            "type": p_type,
            "original_directive": d["text"],
            "media_path": d["media_path"],
            "generated_copy": generated["copy"],
            "hashtags": generated["hashtags"],
            "suggested_time": generated["suggested_time"],
            "scheduled_time": datetime.now().strftime("%Y-%m-%d") + " " + generated["suggested_time"],
            "status": "In Attesa di Approvazione",
            "published_date": null if "null" in globals() else None,
            "engagement": null if "null" in globals() else None,
            "source": d["source"]
        }
        
        db["posts"].append(new_post)
        new_posts.append(new_post)
        count += 1
        
    # Clear unread
    db["unread_directives"] = []
    write_db(db)
    
    return {
        "status": "success",
        "count": count,
        "message": f"Sincronizzazione completata con successo! Elaborati {count} nuovi contenuti multimediali.",
        "new_posts": new_posts
    }

@app.post("/api/inbox/restore")
async def restore_inbox():
    # Helper to restore unread list for testing ease
    db = read_db()
    db["unread_directives"] = [
        {
          "id": "dir_001",
          "subject": "FOTO AUDIZIONE WEEKEND CORSO PROPEDEUTICO",
          "sender": "Marco (Direzione Cagliari)",
          "date": "2026-05-18",
          "text": "Ciao! Ti allego questa foto bellissima dell'audizione dei più piccoli per il corso propedeutico di musical a Cagliari di sabato pomeriggio. Erano emozionatissimi ma sono stati spettacolari, hanno ballato e cantato benissimo. Crea un post Instagram dolce ed emozionante per fare i complimenti a tutti e informare i genitori che le lezioni iniziano a breve e ci sono gli ultimi 3 posti disponibili! Grazie!",
          "media_path": "https://images.unsplash.com/photo-1472653431158-6364773b2a56?auto=format&fit=crop&w=800&q=80",
          "source": "Direzione Email"
        },
        {
          "id": "dir_002",
          "subject": "WhatsApp da Direzione: Video Masterclass Recitazione con Docente Ospite",
          "sender": "Segreteria Cagliari",
          "date": "2026-05-19",
          "text": "Ragazzi, carichiamo questo video breve (Reel) della masterclass esclusiva di recitazione cinematografica che abbiamo tenuto ieri sera qui in sede a Cagliari con il regista e docente ospite di fama nazionale! Gli studenti hanno lavorato sull'immedesimazione emotiva. Scrivi un post carico di ispirazione e professionalità, facendo capire che studiare all'Antiga Armonia/Accademia significa formarsi con i migliori professionisti del settore. Ricorda che sono aperte le ammissioni per il triennale AFAM.",
          "media_path": "https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&w=800&q=80",
          "source": "Direzione WhatsApp"
        }
    ]
    write_db(db)
    return {"status": "success", "message": "Inbox di test ripristinata correttamente!"}

# GEMINI LOGIC OR LOCAL FALLBACK
async def generate_ai_post(directive: str, post_type: str) -> dict:
    system_prompt = """
    Sei il Social Media Specialist intelligente dell'Accademia Internazionale del Musical - sede di Cagliari (gestita dall'associazione Culturale Antiga Armonia).
    Il tuo compito è prendere una direttiva testuale grezza inviata dalla direzione (e-mail o messaggio WhatsApp) e trasformarla in una proposta di post o Reel Instagram di eccezionale livello.
    
    Regole di scrittura:
    1. Scrivi copy emozionanti, carichi di energia, caldi e accoglienti, alternando toni professionali per i corsi formali (AFAM) e toni gioiosi per i più piccoli.
    2. Utilizza le emoji in modo creativo all'inizio delle frasi ed evita blocchi pesanti di testo: usa elenchi puntati o spaziature.
    3. Fai sempre riferimento alla sede di Cagliari e all'Accademia.
    4. Genera una stringa contenente 6-8 hashtag strategici ed esclusivi (es. #AccademiaDelMusical #AntigaArmonia #MusicalCagliari #AFAMCagliari #TeatroCagliari #CagliariEventi).
    5. Consiglia un orario di pubblicazione ottimale per Instagram (es. '13:00' se è pausa pranzo, '18:45' se è fine giornata).
    
    Devi restituire OBBLIGATORIAMENTE ed ESCLUSIVAMENTE un oggetto JSON valido con queste tre chiavi:
    1. "copy": il testo descrittivo del post (escluso il blocco hashtag).
    2. "hashtags": la stringa contenente tutti gli hashtag proposti separati da un singolo spazio.
    3. "suggested_time": l'orario consigliato nel formato HH:MM.
    
    Rispondi solo con il codice JSON pulito, senza blocchi di codice markdown o testo introduttivo.
    """
    
    if gemini_active:
        try:
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                generation_config={"response_mime_type": "application/json"}
            )
            prompt = f"DIRETTIVA DIREZIONE:\n\"{directive}\"\n\nFORMATO RICHIESTO: {post_type}\n\nGenera ora l'oggetto JSON:"
            response = model.generate_content([system_prompt, prompt])
            
            clean_res = response.text.strip()
            res_obj = json.loads(clean_res)
            
            return {
                "copy": res_obj.get("copy", "").strip(),
                "hashtags": res_obj.get("hashtags", "").strip(),
                "suggested_time": res_obj.get("suggested_time", "18:00")
            }
        except Exception as e:
            logger.error(f"Errore Gemini in generate_ai_post: {e}")
            return generate_mock_post(directive, post_type)
    else:
        return generate_mock_post(directive, post_type)

def generate_mock_post(directive: str, post_type: str) -> dict:
    directive_lower = directive.lower()
    
    if "piccoli" in directive_lower or "propedeutico" in directive_lower or "bambini" in directive_lower:
        copy = "✨ SOGNI IN SCENA! COMPLIMENTI AI NOSTRI PICCOLI PERFORMER! ✨\n\nSabato pomeriggio la nostra sede di Cagliari si è riempita di sorrisi, canti e balli grazie all'audizione del nostro Corso Propedeutico di Musical! 🩰🎤\n\nIrenostri giovanissimi candidati sono stati semplicemente spettacolari: emozionati ma carichi di talento ed energia contagiosa! Bravissimi tutti!\n\n🚨 ATTENZIONE GENITORI: Le lezioni inizieranno a brevissimo e rimangono solo gli ULTIMI 3 POSTI DISPONIBILI per completare la classe! Scrivici subito in DM per riservare lo spazio al tuo piccolo artista!"
        hashtags = "#MusicalPropedeutico #BambiniCagliari #DanzaBambini #TeatroCagliari #PiccoliTalenti #CagliariScuola #AntigaArmonia #AccademiaMusical"
        suggested_time = "17:30"
    elif "masterclass" in directive_lower or "cinema" in directive_lower or "regista" in directive_lower:
        copy = "🎬 L'EMOZIONE DEL GRANDE CINEMA IN ACCADEMIA! 🎭\n\nIeri sera i ragazzi della nostra sede di Cagliari hanno vissuto un'esperienza indimenticabile: una Masterclass esclusiva di recitazione cinematografica guidata da un regista di fama nazionale!\n\nUn viaggio intenso dentro l'immedesimazione emotiva e la verità davanti alla telecamera. Studiare all'Antiga Armonia significa formarsi con i migliori professionisti, per fare del talento una solida professione.\n\n🌟 Vuoi un percorso di livello universitario? Le ammissioni per il nostro Triennale Accademico AFAM sono aperte! Fissa la tua audizione conoscitiva gratuita!"
        hashtags = "#CinemaCagliari #RecitazioneCinematografica #MasterclassTeatro #FormazioneProfessionale #AFAMCagliari #AttoriSardi #AccademiaDelMusical"
        suggested_time = "20:00"
    else:
        copy = f"✨ NUOVO AGGIORNAMENTO DALL'ACCADEMIA DI CAGLIARI! ✨\n\nEcco l'ultimo bellissimo contenuto dai nostri corsi professionali di canto, recitazione e danza! La passione dei nostri allievi è il motore che rende speciale l'Accademia Internazionale del Musical.\n\nSegui i nostri canali per non perdere le date delle audizioni, gli spettacoli e gli open day gratuiti.\n\nDirettiva elaborata:\n{directive[:120]}..."
        hashtags = "#AccademiaDelMusical #AntigaArmonia #MusicalCagliari #CagliariLive #CorsiProfessionali #TeatroSardegna"
        suggested_time = "14:00"
        
    return {
        "copy": copy,
        "hashtags": hashtags,
        "suggested_time": suggested_time
    }

if __name__ == "__main__":
    import uvicorn
    # Avvia sulla porta 8083 per evitare conflitti con l'hub principale (8081) e il voice bot (8082)
    uvicorn.run("app:app", host="127.0.0.1", port=8083, reload=True)
