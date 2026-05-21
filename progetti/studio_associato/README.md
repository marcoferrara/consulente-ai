# Studio Associato — RAG AI Match Engine 

Prototipo pronto all'uso e interattivo ad alta fedeltà di un motore **RAG AI** dedicato a **Studi Associati, Commercialisti e Consulenti d'Impresa**. La piattaforma effettua il matching semantico tra i bandi di finanziamento pubblici attivi (Regione Sardegna, bandi nazionali ed europei) e i profili delle aziende clienti registrate in anagrafica studio.

---

## 🚀 Caratteristiche Principali

1. **RAG AI Semantic Search (Simulata):** Consente al professionista di digitare interrogazioni semantiche in linguaggio naturale (es. *"Cerco fondi per digitalizzare un hotel"* o *"Agevolazioni giovani agricoltori in Barbagia"*) identificando all'istante il bando ideale con tasso di coerenza percentuale.
2. **Matching Incrociato Automatico:** Verifica in frazioni di secondo:
   - Coerenza del codice **ATECO** della ditta con i requisiti del bando.
   - Dimensione aziendale (**PMI**, **Micro**, **Grande**).
   - Localizzazione geografica strategica (es. presenza in **Area ZES sarda**).
   - Parametri anagrafici d'impresa (es. età del titolare < 41 anni per misure giovani).
3. **Generazione di Alert su Canali di Contatto:** Crea bozze personalizzate pronte all'invio per l'imprenditore:
   - **Bozza WhatsApp Business** (con markdown, emoji e link diretto di prenotazione call).
   - **Bozza Email Formale** (con l'analisi tecnica di idoneità dettagliata pre-compilata).
4. **Dual Mode (Online Live / Offline Mock):**
   - **Live API:** Dialoga in tempo reale tramite richieste HTTP JSON con il server FastAPI.
   - **Mock Locale (Zero Dipendenze):** Se il server non è avviato, il frontend commuta automaticamente allo stato offline, eseguendo l'intero algoritmo di matching in JavaScript client-side. Funziona perfettamente facendo doppio clic sul file `index.html`!

---

## 🛠️ Come Avviarlo in Modalità Live API

### 1. Installazione delle Dipendenze Python
Apri il terminale all'interno di questa directory ed esegui:
```bash
pip install -r requirements.txt
```

### 2. Avvio del Server FastAPI
Avvia il backend di matching AI (è configurato sulla porta **8001** per evitare conflitti con altre applicazioni del portfolio):
```bash
python app.py
```
Il server visualizzerà un output simile a questo:
```
INFO:     Started server process [65842]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

### 3. Apertura del Frontend
Apri semplicemente il file `index.html` all'interno del tuo browser.
L'indicatore in alto a destra mostrerà **ONLINE (Live API)** in verde, a indicare che la dashboard sta interrogando con successo il server locale.

---

## 📂 Struttura del Progetto

- [index.html](file:///Users/marco/Claude%20Code/Consulente%20AI/progetti/studio_associato/index.html): L'interfaccia utente (HTML5/CSS3/Vanilla JS) scura con finiture dorate e glassmorphism.
- [app.py](file:///Users/marco/Claude%20Code/Consulente%20AI/progetti/studio_associato/app.py): Server API FastAPI che implementa le rotte `/api/match`, `/api/search` e `/api/send_alert`.
- [config.py](file:///Users/marco/Claude%20Code/Consulente%20AI/progetti/studio_associato/config.py): Database simulato contenente 4 bandi reali sardi e 7 aziende clienti (es. *Viticoltori Argiolas, Agriturismo Su Gologone, Pastificio La Sorgente*).
- [requirements.txt](file:///Users/marco/Claude%20Code/Consulente%20AI/progetti/studio_associato/requirements.txt): File dei requisiti Python.

---

## 🎓 Scenari Demo Consigliati per i Clienti

1. **Scenario Digitalizzazione PMI:**
   - Clicca sul preset **💻 POR FESR Digitalizzazione PMI** (o digita *"digitalizzazione"* nella barra di ricerca).
   - Noterai come il sistema identifichi come perfettamente idonee aziende di servizi/software (Sardinia Tech, Boutique Hotel, Pastificio Sorgente), mentre escluderà automaticamente gli allevamenti.
2. **Scenario Agricoltura Giovani:**
   - Clicca sul preset **🌾 PSR Giovani Agricoltori**.
   - Il sistema calcolerà l'idoneità immediata per la *Cooperativa Barbagia Pastori* (titolare di 34 anni, limite < 41), ma segnalerà come **Esclusa** l'azienda *Argiolas Viticoltori* perché il titolare ha superato il limite di età (52 anni).
3. **Scenario ZES Unica:**
   - Clicca sul preset **🏭 Credito ZES Unica Sardegna**.
   - Il sistema identificherà come idonee al 100% le *Officine Meccaniche Sarde* (localizzate nella Zona Industriale Tossilo a Macomer, area ZES), spiegando nel dettaglio il motivo geografico del match.
