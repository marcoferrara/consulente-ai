# SardiniaCraft AI — Copilota AI E-Commerce & Spedizioni Internazionali

Questo è il prototipo interattivo sviluppato per il caso **Laboratorio Artistico d'Eccellenza** (artigianato artistico sardo, filigrana, tessitura, ceramiche).

Risolve il problema della digitalizzazione e vendita all'estero di pezzi unici dell'artigianato sardo di altissimo valore (es. tappeti sardi, oreficeria filigrana) automatizzando la descrizione poetica/SEO in più lingue per Shopify e calcolando all'istante i dazi/costi doganali per i clienti esteri.

---

## 🚀 Come Eseguire il Progetto

Il prototipo è dotato di un'architettura **Dual Mode** che gli permette di funzionare in tempo reale sia offline (Mock client-side) che online (Live API).

### 1. Avviare il Server API Locale (Raccomandato)
Per testare il prototipo in modalità dinamica reale connessa al server:

1. Assicurati di trovarti nella cartella `progetti/laboratorio_artistico/`:
   ```bash
   cd progetti/laboratorio_artistico
   ```
2. Installa le dipendenze indicate nel file `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
3. Lancia il server di backend FastAPI:
   ```bash
   python3 app.py
   ```
Il server si avvierà su `http://127.0.0.1:8085`.

### 2. Accedere alla Dashboard
*   **Dalla Landing Page Principale:** Apri `Consulente AI/index.html`, seleziona il caso **"Laboratorio Artistico"** (artigianato) e fai clic su **"Risolvi con l'AI"**. Al termine della simulazione, fai clic sul pulsante dorato **"Avvia Prototipo Reale"**.
*   **Direttamente:** Apri il file `progetti/laboratorio_artistico/index.html` nel browser.

---

## 💎 Scenari Demo da Mostrare al Cliente

### Scenario 1: Scanner Multimodale Vision AI & Copywriting
1. Seleziona uno dei tre pezzi d'eccellenza preimpostati:
   *   **Fede Sarda Classica** (Gioiello tradizionale)
   *   **Tappeto di Mogoro con Pavoncelle** (Tessitura artistica)
   *   **Brocca della Sposa** (Ceramica smaltata al tornio)
2. Fai clic su **"Analizza Pezzo con Vision AI"**: l'interfaccia avvia un'animazione laser che simula l'analisi visiva delle trame e dei materiali.
3. Al termine dell'analisi, il pannello centrale si popola con:
   *   **Titolo Emozionale & SEO**
   *   **Storytelling del Simbolo**: Spiega la storia culturale millenaria del manufatto sardo (es. la favoncella sarda o il nido d'ape).
   *   **Shopify Metadata & Tag**
4. Clicca sulle tab **English 🇬🇧** o **Deutsch 🇩🇪**: vedrai l'intero blocco copywriting tradursi all'istante per il mercato estero.
5. Clicca su **"Sincronizza su Shopify"**: simulerà il caricamento del catalogo online in tempo reale.

### Scenario 2: Assistente Spedizioni Internazionali AI & Dogane
1. Nel pannello di destra, fai clic su una delle domande frequenti dei clienti esteri (es. Emily da New York o Kenji da Tokyo).
2. L'AI analizza il peso dell'oggetto e il paese, e formula in pochi secondi una risposta impeccabile nella lingua del cliente.
3. Il calcolatore in basso mostra:
   *   La tariffa del corriere espresso.
   *   Il tempo di transito.
   *   Le informazioni doganali specifiche (es. *US De Minimis* per esenzione dazi sotto $800 negli USA, mercati UE in Germania, ecc.).
4. Digita una domanda personalizzata nella barra in basso (es. *"Spedite in Germania?"* o *"Is shipping to Japan insured?"*) per vedere l'assistente rispondere dinamicamente.
