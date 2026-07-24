import sys
import time
import requests

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

URL = "http://localhost:8010/webhook/whatsapp"
USER_ID = "+393401122334"
USER_NAME = "Marco"


def send_message(message: str):
    payload = {"user_id": USER_ID, "message": message, "user_name": USER_NAME}
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
                print("\n🚨 [SISTEMA]: Handover attivato! Il proprietario prende in mano la conversazione.")
            print("=" * 50)
            return active
        else:
            print(f"Errore del server: Status {response.status_code}")
    except Exception as e:
        print(f"Errore di connessione: {e}")
    return False


def main():
    print("=" * 60)
    print("      SIMULATORE CHAT WHATSAPP - GITTY&STELLA")
    print("=" * 60)
    print("Il server FastAPI deve essere attivo su localhost:8010.")
    time.sleep(1.5)

    send_message("Ciao! Avete disponibilità dal 20 al 25 agosto per 2 persone?")
    time.sleep(3.5)

    send_message("Perfetto, vorrei prenotare. Mi chiamo Marco, email marco@example.com, telefono +393401122334.")
    time.sleep(3.5)

    send_message("Vorrei parlare con il proprietario per una richiesta speciale.")
    time.sleep(2)


if __name__ == "__main__":
    main()
