# notifier.py
# Composizione e invio del report finale via WhatsApp e/o email

import os
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


def formatta_messaggio(
    telaio: str,
    marchio: str,
    risultati: list[dict],
    cliente: Optional[str] = None,
    tempo_secondi: Optional[float] = None,
) -> str:
    """
    Compone il messaggio WhatsApp con tutti i codici trovati per ogni ricambio.
    """
    righe = []

    # Intestazione
    righe.append("🚛 *RICERCA CODICI ORIGINALI*")
    righe.append("━━━━━━━━━━━━━━━━━━━━━")
    if cliente:
        righe.append(f"👤 Cliente: {cliente}")
    righe.append(f"🔩 Telaio: `{telaio}`")
    righe.append(f"🏷️ Marchio: *{marchio}*")
    righe.append("")

    # Risultati per ogni ricambio
    for r in risultati:
        nome = r.get("ricambio", "Ricambio sconosciuto")
        trovato = r.get("trovato", False)
        codici = r.get("codici", [])
        note = r.get("note")

        righe.append(f"📦 *{nome.upper()}*")

        if not trovato or not codici:
            righe.append("  ⚠️ _Non trovato nel catalogo_")
        else:
            righe.append("  Codici originali:")
            for c in codici:
                codice = c.get("codice", "")
                stato = c.get("stato", "")
                if stato == "attuale":
                    righe.append(f"  • *{codice}* (codice attuale ✅)")
                elif "sostituito" in stato.lower():
                    righe.append(f"  • {codice} _(sostituito)_")
                else:
                    righe.append(f"  • {codice}")

        if note:
            righe.append(f"  📝 _{note}_")

        righe.append("")

    # Piede messaggio
    righe.append("━━━━━━━━━━━━━━━━━━━━━")
    if tempo_secondi:
        minuti = int(tempo_secondi // 60)
        secondi = int(tempo_secondi % 60)
        righe.append(f"⏱ Ricerca completata in {minuti}m {secondi}s")
    righe.append("_Generato da Agente Ricerca Ricambi Truck_")

    return "\n".join(righe)


async def invia_whatsapp(testo: str, numero: Optional[str] = None) -> bool:
    """
    Invia il report via WhatsApp tramite CallMeBot.
    Usa COMPANY_DESTINATION_NUMBER dal .env se numero non specificato.
    """
    dest = numero or os.getenv("COMPANY_DESTINATION_NUMBER")
    callmebot_key = os.getenv("CALLMEBOT_API_KEY")

    if not dest:
        logger.warning("Numero destinatario WhatsApp non configurato — messaggio non inviato")
        logger.info(f"--- ANTEPRIMA MESSAGGIO ---\n{testo}\n---")
        return False

    if not callmebot_key:
        logger.warning("CALLMEBOT_API_KEY non configurata — invio simulato")
        logger.info(f"--- ANTEPRIMA MESSAGGIO ---\n{testo}\n---")
        return False

    # CallMeBot non supporta markdown avanzato — pulizia minimale
    testo_clean = testo.replace("`", "")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.callmebot.com/whatsapp.php",
                params={"phone": dest, "text": testo_clean, "apikey": callmebot_key},
                timeout=15.0,
            )
            if resp.status_code == 200:
                logger.info("Report WhatsApp inviato con successo tramite CallMeBot")
                return True
            else:
                logger.error(f"CallMeBot errore: {resp.status_code} — {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Errore invio WhatsApp: {e}")
        return False


async def invia_screenshot_whatsapp(percorso_file: str, numero: Optional[str] = None) -> bool:
    """
    Invia uno screenshot via gateway WhatsApp (Z-API / Evolution API).
    CallMeBot non supporta immagini — richiede gateway con supporto media.
    """
    dest = numero or os.getenv("COMPANY_DESTINATION_NUMBER")
    gateway_url = os.getenv("WHATSAPP_GATEWAY_URL")
    instance_id = os.getenv("WHATSAPP_INSTANCE_ID")
    token = os.getenv("WHATSAPP_TOKEN")

    if not gateway_url or not dest:
        logger.info(f"Screenshot salvato localmente: {percorso_file} (gateway non configurato)")
        return False

    try:
        with open(percorso_file, "rb") as f:
            immagine_bytes = f.read()

        import base64
        img_b64 = base64.b64encode(immagine_bytes).decode()

        headers = {"Authorization": f"Bearer {token}"} if token else {}
        endpoint = f"{gateway_url.rstrip('/')}/message/sendImage/{instance_id}" if instance_id \
                   else f"{gateway_url.rstrip('/')}/send-image"

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                endpoint,
                json={"number": dest, "image": img_b64, "caption": "Screenshot EPC"},
                headers=headers,
                timeout=20.0,
            )
            if resp.status_code in (200, 201):
                logger.info(f"Screenshot inviato via WhatsApp: {percorso_file}")
                return True
            else:
                logger.error(f"Errore invio screenshot: {resp.status_code} — {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Errore invio screenshot WhatsApp: {e}")
        return False
