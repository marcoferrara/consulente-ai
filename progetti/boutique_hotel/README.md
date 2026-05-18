# AI Concierge Prototype - Boutique Hotel S'Antiga

Questo prototipo simula il server di backend per l'assistente virtuale su WhatsApp del **Boutique Hotel S'Antiga Charme & Spa** in Sardegna. 

Il sistema implementa:
1. **Webhook FastAPI**: Ricezione e routing dei messaggi (simulazione WhatsApp).
2. **PMS API Connector (Mock)**: Funzioni per verificare tariffe, controllare la disponibilità live e creare blocchi provvisori sulle camere.
3. **Function Calling / Tool Use**: L'AI riconosce in autonomia quando è il caso di interrogare il PMS per rispondere al cliente.
4. **Handover Umano**: Scatta se il cliente richiede esplicitamente un operatore, esprime frustrazione, o per preventivi speciali ad alto valore.

## Struttura Progetto
* `app.py`: Server principale con i router FastAPI e l'orchestratore OpenAI.
* `config.py`: Parametri, database mock delle camere e configurazioni.
* `requirements.txt`: Dipendenze necessarie.

## Come avviarlo
1. Assicurati di avere Python installato.
2. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```
3. Imposta la tua chiave OpenAI (facoltativo, per l'esecuzione reale):
   ```bash
   # Windows PowerShell
   $env:OPENAI_API_KEY="la-tua-chiave-qui"
   ```
4. Avvia il server:
   ```bash
   uvicorn app:app --reload
   ```

Il server sarà accessibile su `http://localhost:8000`. Puoi simulare messaggi inviando richieste POST a `http://localhost:8000/webhook/whatsapp`.
