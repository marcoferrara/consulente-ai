# Guida all'Installazione e Configurazione di Ollama con Vision su macOS

Questa guida spiega passo-passo come installare **Ollama**, configurare i modelli **Vision** e abilitare i permessi necessari su macOS per poter eseguire l'agente locale di **ricambi_truck** (`local_agent.py`).

---

## 🛠️ Step 1: Installare Ollama su macOS

Per eseguire i modelli in locale, abbiamo bisogno di Ollama. Ci sono due modi principali per installarlo su Mac:

### Opzione A: Installazione Manuale (Consigliata)
1. Vai su [ollama.com/download](https://ollama.com/download) e scarica l'applicazione per macOS.
2. Estrai il file `.zip` scaricato.
3. Trascina l'applicazione **Ollama** nella cartella **Applicazioni** (Applications) del tuo Mac.
4. Avvia Ollama dalla cartella Applicazioni. Comparirà l'icona di Ollama nella barra dei menu in alto a destra.

### Opzione B: Installazione via Homebrew (Alternativa per sviluppatori)
Se usi Homebrew, apri il Terminale e digita:
```bash
brew install ollama
```
Per avviarlo come servizio in background:
```bash
brew services start ollama
```

---

## 🧠 Step 2: Scaricare il Modello Vision

L'agente locale di `ricambi_truck` utilizza un modello in grado di vedere ed analizzare gli screenshot per localizzare i pulsanti su cui cliccare. Il modello predefinito è `qwen2-vl` (Qwen 2 Vision Language).

Apri il Terminale e avvia il download del modello:

```bash
# Scarica ed avvia il modello predefinito (Qwen2-VL)
ollama run qwen2-vl
```

> [!TIP]
> * Per Mac con 8GB o 16GB di RAM unificata, il modello predefinito `qwen2-vl` (che scarica la versione da 7B parametri) o `llama3.2-vision` (11B parametri) funzionano bene.
> * Se noti rallentamenti o problemi di memoria, puoi provare una versione più leggera come:
>   `ollama run qwen2-vl:2b`
>   (e poi passare il parametro `--model qwen2-vl:2b` quando lanci lo script).

Per verificare che il modello sia stato scaricato correttamente, digita:
```bash
ollama list
```
Dovresti vedere nell'elenco `qwen2-vl` (o il modello da te scelto).

---

## 🔒 Step 3: Configurare i Permessi di macOS (CRUCIALE)

L'agente locale interagisce fisicamente con il tuo computer: cattura la schermata (tramite `mss`/`pillow`) e sposta/clicca con il mouse (tramite `pyautogui`). **macOS blocca queste azioni per impostazione predefinita per motivi di sicurezza.**

Devi autorizzare esplicitamente l'applicazione da cui lanci lo script (es. **Terminale**, **iTerm**, **VS Code**, o **Cursor**):

1. Apri le **Impostazioni di Sistema** (System Settings) del tuo Mac.
2. Vai su **Privacy e Sicurezza** (Privacy & Security).
3. Configura le seguenti sezioni:
   * **Accessibilità** (Accessibility): Clicca sul pulsante `+`, inserisci la password del Mac e aggiungi l'applicazione che usi per l'esecuzione dello script (es. *Terminal.app*, *VS Code*, *Cursor*). Assicurati che l'interruttore sia attivo.
   * **Registrazione dello schermo** (Screen Recording): Fai lo stesso procedimento e aggiungi l'applicazione alla lista per consentire la cattura degli screenshot della griglia.
4. **Riavvia l'applicazione** (chiudila completamente e riaprila) per rendere effettivi i nuovi permessi.

---

## 🐍 Step 4: Configurare l'Ambiente Python

Assicurati di trovarti nella cartella del progetto e installa le librerie Python richieste:

1. Apri il Terminale e posizionati nella cartella del progetto:
   ```bash
   cd "/Users/marco/Claude Code/Consulente AI/progetti/ricambi_truck"
   ```
2. Installa le dipendenze contenute nel file `requirements.txt`:
   ```bash
   pip3 install -r requirements.txt
   ```

---

## 🚀 Step 5: Esecuzione dell'Agente Locale

Ora puoi avviare l'agente. Lo script `local_agent.py` accetta diversi parametri da riga di comando.

### 1. Test in modalità Sicura (Dry-Run)
Prima di lasciare che l'agente sposti il mouse, esegui un test di simulazione. Lo script ti mostrerà le azioni che avrebbe eseguito senza effettivamente effettuarle:
```bash
python3 local_agent.py --brand iveco --vin "BOLOGNA TORINO 096 DOMODOSSOLA FIRENZE" --part "alternatore" --dry-run
```

### 2. Esecuzione Reale
Per avviare l'automazione reale che muove il mouse e clicca sullo schermo:
```bash
python3 local_agent.py --brand iveco --vin "BT096DF" --part "alternatore"
```

### 3. Opzioni Aggiuntive
* **Specificare un modello personalizzato**: Se hai scaricato un modello diverso (es. `llama3.2-vision` o `qwen2-vl:2b`), indicalo con il flag `--model`:
  ```bash
  python3 local_agent.py --brand iveco --vin "BT096DF" --part "alternatore" --model llama3.2-vision
  ```
* **Connessione automatica al Desktop Remoto**: Se hai bisogno di collegarti ad AnyDesk prima di avviare il catalogo, usa il flag `--connect`. Questo leggerà le istruzioni da `istruzioni/connessione.yaml` ed eseguirà la fase di login:
  ```bash
  python3 local_agent.py --brand iveco --vin "BT096DF" --part "alternatore" --connect
  ```

---

## ⚠️ Avvertenza per la Sicurezza (Fail-Safe)

L'agente implementa un sistema di **Fail-Safe** nativo di PyAutoGUI:
* In caso l'agente perda il controllo o inizi a fare clic errati, **spingi con forza il cursore del mouse in uno dei quattro angoli dello schermo**.
* Questo interromperà immediatamente l'esecuzione dello script lanciando un'eccezione di sicurezza (`FailSafeException`).
