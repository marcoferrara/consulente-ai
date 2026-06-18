# Guida alla Configurazione: Migrazione Notion -> Google Drive

Questa guida ti accompagna passo-passo nella configurazione delle API di **Notion** e **Google Drive** necessarie per far funzionare lo script `sposta_su_drive.py`.

---

## 🛠️ Step 1: Configura l'Integrazione Notion

Per consentire allo script di leggere le tue pagine Notion:

1. Accedi alla dashboard delle integrazioni Notion: [Notion Developers - My Integrations](https://www.notion.so/my-integrations).
2. Clicca su **+ New integration** (Nuova integrazione).
3. Compila i campi:
   * **Associated workspace**: seleziona lo spazio di lavoro contenente la pagina da migrare.
   * **Name**: inserisci un nome (es. *Google Drive Migrator*).
   * **Logo**: (opzionale).
4. Clicca su **Submit** in fondo alla pagina.
5. Nella scheda **Secrets**, clicca su **Show** e copia il **Internal Integration Token** (inizia con `secret_...`). Lo userai quando avvierai lo script.

### 🔗 Abilita l'accesso alla pagina Notion:
Notion vieta l'accesso ai tuoi dati per impostazione predefinita. Devi autorizzare esplicitamente l'integrazione a vedere la pagina:
1. Apri la pagina principale di Notion che desideri spostare su Google Drive.
2. Clicca sul pulsante con i tre puntini **`...`** in alto a destra.
3. Seleziona **Connessioni** (Connections) -> **Aggiungi connessione** (Add Connection).
4. Cerca e seleziona il nome dell'integrazione che hai creato (*Google Drive Migrator*).
5. Conferma l'accesso. Ora l'integrazione ha accesso a quella pagina e a tutte le sue sottopagine.

---

## 🔑 Step 2: Ottieni le Credenziali Google Drive (credentials.json)

Per consentire allo script di caricare i file sul tuo account Google Drive:

1. Accedi alla [Google Cloud Console](https://console.cloud.google.com/).
2. **Crea un Progetto**:
   * Clicca sul menu a tendina dei progetti in alto a sinistra (accanto alla scritta Google Cloud).
   * Clicca su **Nuovo progetto** (New Project).
   * Assegna un nome (es. *Notion Migrator*) e clicca su **Crea**. Assicurati che sia selezionato questo progetto una volta pronto.
3. **Abilita la Drive API**:
   * Clicca sul menu di navigazione a sinistra (tre linee) e vai su **API e servizi** -> **Libreria** (Library).
   * Cerca **Google Drive API**.
   * Clicca sul risultato e poi premi **Abilita** (Enable).
4. **Configura la Schermata di Consenso OAuth**:
   * Dal menu a sinistra, vai su **API e servizi** -> **Schermata consenso OAuth** (OAuth Consent Screen).
   * Seleziona **Esterno** (External) e clicca su **Crea**.
   * Inserisci le informazioni richieste:
     * **Nome applicazione**: *Notion Migrator*.
     * **Email di supporto**: seleziona il tuo indirizzo Gmail.
     * **Informazioni di contatto dello sviluppatore**: inserisci di nuovo la tua email.
   * Clicca su **Salva e continua**.
   * Nella scheda **Scopi (Scopes)**, non modificare nulla e clicca su **Salva e continua**.
   * **IMPORTANTISSIMO**: Nella scheda **Utenti di test (Test users)**, clicca su **+ ADD USERS** (Aggiungi utenti) e inserisci la tua email Gmail personale. *Senza questo passaggio, non sarai in grado di autenticarti!*
   * Clicca su **Salva e continua** e infine su **Torna alla dashboard**.
5. **Crea le Credenziali dell'Applicazione Desktop**:
   * Clicca su **Credenziali** (Credentials) nel menu a sinistra.
   * Clicca su **+ Crea credenziali** (Create credentials) in alto e seleziona **ID client OAuth**.
   * Seleziona **Applicazione desktop** (Desktop app) come tipo di applicazione.
   * Inserisci un nome (es. *Drive Uploader*) e clicca su **Crea**.
6. **Scarica il file JSON**:
   * Apparirà una finestra di conferma. Chiudila.
   * Nella tabella *ID client OAuth 2.0*, vedrai la credenziale appena creata. Clicca sull'icona di download (una freccia rivolta verso il basso) all'estrema destra della riga.
   * Rinomina il file scaricato in **`credentials.json`** e posizionalo all'interno di questa cartella: `/Users/marco/Claude Code/Consulente AI/`.

---

## 🚀 Step 3: Avvia lo Script

1. Apri il terminale del tuo Mac.
2. Naviga nella cartella del progetto:
   ```bash
   cd "/Users/marco/Claude Code/Consulente AI"
   ```
3. Avvia lo script digitando:
   ```bash
   python3 sposta_su_drive.py
   ```
4. Lo script ti chiederà di inserire:
   * **Notion Integration Token**: Incolla il token `secret_...` ottenuto al punto 1.
   * **Notion Page ID**: Copia l'intero URL della pagina Notion dalla barra del browser e incollalo. Lo script è intelligente ed estrarrà l'ID della pagina in modo automatico.
   * **Google Drive Folder ID**: Se vuoi caricare tutto all'interno di una cartella specifica di Google Drive, incolla il suo ID (lo trovi alla fine dell'URL quando apri la cartella nel browser di Drive, es. `https://drive.google.com/drive/folders/IL_TUO_ID`). Altrimenti, **premi semplicemente Invio** per caricare nella Root principale del tuo Drive.
5. **Autenticazione nel Browser**:
   * All'avvio, lo script aprirà automaticamente una scheda del browser per l'autenticazione con Google.
   * Seleziona il tuo account Google (quello aggiunto come *Test User* nello Step 2).
   * Google potrebbe mostrare un avviso di sicurezza (*Google non ha verificato questa app*). Fai clic su **Avanzate** (in basso) e poi su **Vai a Notion Migrator (non sicura)** per procedere.
   * Clicca su **Continua** per concedere i permessi di scrittura su Google Drive.
6. Una volta completato il login nel browser, puoi chiudere la scheda. Lo script inizierà a scaricare le pagine Notion (comprese le immagini integrate codificate in Base64) e a caricarle su Drive ricreando la gerarchia ed eliminando istantaneamente i file temporanei locali.
7. I parametri inseriti verranno salvati in un file `.env` e le credenziali di accesso Google in `token.json`, così per le esecuzioni successive non ti verrà chiesto alcun dato aggiuntivo!
