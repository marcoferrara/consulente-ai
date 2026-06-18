# Guida all'Installazione e Configurazione di Ollama con Vision su Windows

Questa guida spiega passo-passo come installare **Ollama**, configurare i modelli **Vision** e preparare l'ambiente di esecuzione per l'agente locale di **ricambi_truck** (`local_agent.py`) su un PC con sistema operativo **Windows**.

---

## 🛠️ Step 1: Installare Ollama su Windows

1. Vai sul sito ufficiale: [ollama.com/download](https://ollama.com/download) e clicca sull'icona di **Windows**.
2. Scarica il file installer **`OllamaSetup.exe`**.
3. Fai doppio clic sul file scaricato per avviare l'installazione e segui la procedura guidata (richiede pochissimi secondi).
4. Al termine dell'installazione, Ollama si avvierà automaticamente. Noterai l'icona di Ollama (l'icona a forma di lama) nell'area di notifica di Windows (in basso a destra, vicino all'orologio).

---

## 🧠 Step 2: Scaricare il Modello Vision

L'agente locale di `ricambi_truck` necessita di un modello in grado di "vedere" gli screenshot. Il modello predefinito è **`qwen2.5vl`**.

1. Apri il **Prompt dei comandi** (CMD) o **PowerShell** sul tuo PC Windows.
2. Esegui il comando di download ed esecuzione:
   ```cmd
   ollama run qwen2.5vl
   ```
3. Attendi il completamento del download (circa 4.7 GB). Una volta terminato, potrai fare una domanda di prova direttamente nel terminale. Digita `/bye` per uscire dalla chat interattiva.

> [!TIP]
> * Se il tuo computer Windows non ha una scheda video dedicata (GPU Nvidia) o ha meno di 16GB di RAM, il modello da 7B parametri potrebbe risultare lento.
> * In questo caso, puoi scaricare una versione molto più leggera (circa 1.7 GB):
>   `ollama run qwen2.5vl:3b`
>   (e poi passare il parametro `--model qwen2.5vl:3b` quando avvii l'agente).

Per verificare i modelli scaricati sul tuo PC Windows:
```cmd
ollama list
```

---

## 🔑 Step 3: Permessi e Privilegi UAC su Windows (CRUCIALE)

A differenza di macOS che usa i permessi di "Accessibilità", Windows utilizza il controllo **UAC (User Account Control)** e la protezione **UIPI (User Interface Privilege Isolation)**.

> [!IMPORTANT]
> Se il programma di Desktop Remoto (es. **AnyDesk**, **TeamViewer**, o **RDP**) o il catalogo ricambi che vuoi controllare sono avviati come **Amministratore**, Windows impedirà a Python e PyAutoGUI di simulare i clic e la tastiera su quelle finestre a meno che anche il terminale non sia elevato.

### Come procedere per evitare che l'agente si blocchi:
1. Chiudi tutti i terminali standard.
2. Fai clic sul menu Start di Windows e cerca **"Prompt dei comandi"** o **"PowerShell"**.
3. Fai clic destro sul programma e seleziona **"Esegui come amministratore"** (Run as administrator).
4. Utilizza questo terminale elevato per installare le dipendenze e lanciare l'agente locale.

---

## 🐍 Step 4: Installare Python e le Dipendenze

Se non hai ancora installato Python sul tuo PC Windows:

1. Scarica l'installer per Windows dal sito ufficiale: [python.org](https://www.python.org/downloads/).
2. **IMPORTANTE:** Durante l'installazione, assicurati di spuntare la casella **"Add Python to PATH"** in basso prima di cliccare su "Install Now".
3. Apri il terminale (come amministratore) e verifica l'installazione:
   ```cmd
   python --version
   pip --version
   ```
4. Naviga nella cartella in cui hai posizionato il progetto `ricambi_truck`:
   ```cmd
   cd "C:\Percorso\Della\Tua\Cartella\ricambi_truck"
   ```
5. Installa le librerie necessarie:
   ```cmd
   pip install -r requirements.txt
   ```

---

## 🚀 Step 5: Avvio dell'Agente su Windows

Ora puoi eseguire l'agente locale. I comandi sono simili a quelli di macOS, ma utilizzi `python` invece di `python3`:

### 1. Test in modalità Dry-Run (Sicuro)
Verifica che la griglia e il modello Ollama funzionino senza simulare clic reali:
```cmd
python local_agent.py --brand iveco --vin "BT096DF" --part "alternatore" --dry-run
```

### 2. Esecuzione Reale
Esegui l'automazione completa sulla macchina Windows:
```cmd
python local_agent.py --brand iveco --vin "BT096DF" --part "alternatore"
```

### 3. Opzioni utili
* Se usi il modello leggero da 3B parametri:
  ```cmd
  python local_agent.py --brand iveco --vin "BT096DF" --part "alternatore" --model qwen2.5vl:3b
  ```
* Se vuoi che esegua anche la connessione ad AnyDesk:
  ```cmd
  python local_agent.py --brand iveco --vin "BT096DF" --part "alternatore" --connect
  ```

---

## ⚠️ Arresto d'Emergenza (Fail-Safe)

Se l'agente inizia a fare clic casuali o perdi il controllo del mouse:
* **Spingi con forza il mouse nell'angolo in alto a sinistra (o in uno qualsiasi dei quattro angoli)** dello schermo.
* PyAutoGUI rileverà questo movimento forzato e interromperà immediatamente lo script per motivi di sicurezza (`FailSafeException`).
