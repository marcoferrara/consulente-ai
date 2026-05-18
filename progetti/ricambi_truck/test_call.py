import os
import json
import logging
from dotenv import load_dotenv
import google.generativeai as genai

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Carica configurazione
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Trascrizione telefonica campione per il test
TEST_TRANSCRIPT = """
Assistente: Benvenuto in Ricambi Truck Ferrara! Io sono l'assistente virtuale. Posso raccogliere la tua richiesta così ti richiamiamo subito. Mi dici il tuo nome e per quale azienda chiami?
Cliente: Ciao, sono Giovanni dell'Officina Meccanica Emiliana.
Assistente: Grazie Giovanni. Mi serve la targa o il telaio del camion per favore. Dettamela scandendo le lettere con i nomi delle città.
Cliente: Ciao, sì, allora, la targa è Bologna, Torino, zero nove sei, Domodossola, Firenze. Quindi Bologna, Torino, zero nove sei, Domodossola, Firenze.
Assistente: Perfetto, registrata. Che ricambio ti serve esattamente per questo mezzo?
Cliente: Senti, ho un Iveco Stralis con l'alternatore che ci ha abbandonati, si è bruciato del tutto. Potete verificare se lo avete disponibile da ventiquattro volt?
Assistente: Capito. Il camion è fermo in panne per questa cosa o si tratta di una manutenzione ordinaria?
Cliente: Eh sì, il camion è fermo in autostrada in cantiere, ho il cliente bloccato con il carico, ho bisogno che mi facciate sapere al più presto se ce l'avete a magazzino.
Assistente: Molto bene, ho registrato tutto con urgenza. Sto inviando subito la trascrizione al team dei ricambisti. Ti richiamiamo tra pochissimi minuti! Grazie e a presto!
"""

def parse_with_gemini(transcript: str) -> dict:
    if not GEMINI_API_KEY:
        print("\n❌ ERRORE: GEMINI_API_KEY non trovata nel file .env!")
        return {}

    genai.configure(api_key=GEMINI_API_KEY)
    
    prompt = f"""
Sei l'analista tecnico senior di Ricambi Truck Ferrara. Il tuo compito è analizzare la trascrizione di una telefonata e compilare un JSON strutturato contenente le informazioni chiave per il team di officina.

Presta particolare attenzione alla targa del veicolo. I clienti spesso scandiscono la targa lettera per lettera usando i nomi delle città (es. "Milano Torino due tre quattro Como Domodossola"). Reindirizza queste informazioni ricreando la targa originale in stampatello maiuscolo (es. "MT234CD").
Ad esempio:
- Milano -> M, Torino -> T, Como -> C, Domodossola -> D, Firenze -> F, Bologna -> B, Ancona -> A, Venezia -> V, Genova -> G, ecc.
- Se dicono "zero nove sei" scrivi "096".

Estrai un oggetto JSON con ESATTAMENTE le seguenti chiavi (e nessun altro testo di contorno):
{{
  "cliente": "Nome della persona ed eventuale officina o azienda (es. Mario Rossi - Officina Estense)",
  "targa_telaio_grezza": "Il testo esatto pronunciato dal cliente per la targa o il telaio",
  "targa_telaio_ricostruita": "La targa o il telaio ricostruito in maiuscolo e senza spazi (es. AB123CD)",
  "ricambi_richiesti": ["Lista dei pezzi di ricambio richiesti, es: Soffione sospensione, Alternatore 24V"],
  "urgenza": "Livello di urgenza. Deve essere SOLO uno tra: 'ALTA (Veicolo Fermo)' o 'NORMALE'",
  "sintesi": "Una singola frase sintetica ed efficace che descrive la richiesta del cliente"
}}

Trascrizione della chiamata:
\"\"\"
{transcript}
\"\"\"
"""
    try:
        print("🤖 Invio della trascrizione a Google Gemini 2.5 Flash...")
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text.strip())
    except Exception as e:
        print(f"❌ Errore durante l'elaborazione AI: {e}")
        return {}

def main():
    print("=" * 60)
    print("🚚 TRUCK AI PHONE RESPONDER - SIMULATORE LOCALE 🚚")
    print("=" * 60)
    
    print("\n📝 TRASCRIZIONE CAMPIONE DA ANALIZZARE:")
    print("-" * 50)
    print(TEST_TRANSCRIPT.strip())
    print("-" * 50)
    
    # Esegui parsing
    data = parse_with_gemini(TEST_TRANSCRIPT)
    
    if not data:
        print("\nImpossibile completare la simulazione.")
        return

    print("\n✅ RISULTATO ESTRAZIONE DATI AI (JSON):")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    # Formattazione Report WhatsApp
    ricambi_str = "\n".join([f"  • {r}" for r in data.get("ricambi_richiesti", [])])
    is_alta = "ALTA" in data.get("urgenza", "")
    urg_indicator = "🚨 [URGENTE]" if is_alta else "✉️ [STANDARD]"
    
    print("\n💬 ANTEPRIMA NOTIFICA WHATSAPP AZIENDALE:")
    print("=" * 50)
    print(f"{urg_indicator} *NUOVA RICHIESTA TRUCK AI*")
    print(f"👤 *Cliente:* {data.get('cliente')}")
    print(f"📞 *Telefono:* +39 345 8899123 (Simulato)")
    print(f"🚚 *Targa/Telaio:* `{data.get('targa_telaio_ricostruita')}`")
    print(f"🗣️ _Dettato come: \"{data.get('targa_telaio_grezza')}\"_")
    print(f"🛠️ *Ricambi Richiesti:*")
    print(ricambi_str)
    print(f"⚠️ *Urgenza:* {data.get('urgenza')}")
    print(f"📝 *Sintesi Assistente:* {data.get('sintesi')}")
    print("=" * 50)
    print("\n🎉 Test completato con successo! La targa dettata Bologna Torino 096 Domodossola Firenze è stata ricostruita correttamente in: BT096DF!")

if __name__ == "__main__":
    main()
