# Prototipo Cabina Operativa — SardiniaLogistics AI

Questo prototipo reale ad alta fedeltà mostra una cabina operativa intelligente per una **PMI di Logistica & Distribuzione** operante in Sardegna, con focus sulla risoluzione delle tratte tortuose dell'entroterra (Barbagia, Ogliastra) e la prevenzione dell'out-of-stock nei borghi montani durante eventi ad alto traffico.

---

## 🚀 Caratteristiche del Prototipo

1. **Mappa SVG Operativa Interattiva**: Mappa ad altissimo impatto estetico del centro-est Sardegna, con percorsi dinamici e animati (tratte Cagliari -> Barbagia e Cagliari -> Ogliastra) e indicatori meteo e di viabilità.
2. **Predictive Demand Hub**: Simulatore basato su eventi reali locali (es. *Cortes Apertas* a Mamoiada, *Sagra delle Castagne* ad Aritzo, *Stagione Estiva* a Tortolì) per consigliare le scorte preventive per evitare la saturazione o il sottoscorta.
3. **Simulatore Volumetrico di Carico**: Animazione CSS e 3D che controlla in tempo reale la saturazione del vano di carico e avverte se il bilanciamento pesi è non conforme alle curve di montagna (Gennargentu).
4. **AI Dispatcher Copilot (Chat)**: Assistente virtuale basato su linguaggio naturale collegato al server per rispondere a complesse domande di deviazioni stradali, orari di scarico e gestione imprevisti.

---

## 🛠️ Come Eseguire il Prototipo

Il prototipo è progettato per funzionare in **Dual Mode**:
* **Online (Live API)**: Si connette al server FastAPI in Python sulla porta `8086`.
* **Offline (Mock Locale)**: In assenza del server attivo, il frontend devia in automatico sul database mock interno, garantendo il funzionamento perfetto di ogni singola interazione anche senza terminale attivo.

### Esecuzione con il Server:
1. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```
2. Avvia il server:
   ```bash
   python3 app.py
   ```
3. Visita la pagina su: `http://localhost:8086` o lanciala direttamente tramite la Landing Page principale di **Consulente AI**.
