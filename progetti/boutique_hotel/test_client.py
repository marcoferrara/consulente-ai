import sys
import time
import requests

# Forzo la codifica della console in UTF-8 su Windows per evitare errori con emoji
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass # Fallback per vecchie versioni

URL = "http://localhost:8000/webhook/whatsapp"
USER_ID = "+393401122334"
USER_NAME = "Marco"

def send_message(message: str):
    payload = {
        "user_id": USER_ID,
        "message": message,
        "user_name": USER_NAME
    }
    print(f"\n[Ospite ({USER_NAME})]: {message}")
    print("-" * 50)
    
    try:
        response = requests.post(URL, json=payload)
        if response.status_code == 200:
            res = response.json()
            sender = res.get("sender", "AI")
            reply = res.get("reply", "")
            active = res.get("session_active", True)
            handover = res.get("handover_triggered", False)
            
            print(f"[{sender}]: {reply}")
            if handover:
                print("\n🚨 [SISTEMA]: Handover umano attivato! La chat è stata trasferita alla reception.")
            print("=" * 50)
            return active
        else:
            print(f"Errore del server: Status {response.status_code}")
    except Exception as e:
        print(f"Errore di connessione: {e}")
    return False

def main():
    print("=" * 60)
    print("      SIMULATORE CHAT WHATSAPP - BOUTIQUE HOTEL AI CONCIERGE")
    print("=" * 60)
    print("Questo script simulerà una conversazione reale passo-passo con l'AI Sanna.")
    print("Il server FastAPI è attivo su localhost:8000.")
    time.sleep(1.5)
    
    # Step 1: Richiesta disponibilità camere
    send_message("Ciao! Avete camere libere per due persone a febbraio?")
    time.sleep(3.5)
    
    # Step 2: Richiesta di blocco provvisorio della camera
    send_message("Perfetto! Vorrei bloccare la camera Deluxe Vista Mare a mio nome per 2 notti con colazione inclusa.")
    time.sleep(3.5)
    
    # Step 3: Richiesta operatore umano / preventivo speciale
    send_message("Avete servizi di transfer privato dall'aereoporto di Cagliari?")
    time.sleep(2)

if __name__ == "__main__":
    main()
