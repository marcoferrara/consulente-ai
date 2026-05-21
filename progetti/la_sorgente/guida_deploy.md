# Guida al Deploy Online — La Sorgente (Hub Bandi AI)

Questa guida illustra passo-passo come mettere online l'applicazione unificata **La Sorgente** in produzione. L'applicazione è strutturata per essere flessibile, sicura ed estremamente resiliente ai riavvii dei server cloud.

---

## 📦 1. Preparazione del Pacchetto (Consigliato)

Prima di caricare l'applicazione sul server o su GitHub, esegui lo script di pulizia e packaging automatico:

```bash
python crea_pacchetto.py
```

Questo script genererà un file pulito chiamato `la_sorgente_deploy.zip` escludendo file pesanti o personali (`venv/`, `.env` privato, file caricati nei test, `.DS_Store`). Estrai il contenuto di questo zip nella cartella di lavoro sul server o inizializza il tuo repository Git a partire da questo archivio.

---

## ☁️ 2. Deploy su Google Cloud Run & Storage FUSE (Consigliato ⭐ - Firebase-ready)

Google Cloud Run consente di avviare il container dell'applicazione in modalità serverless. Integrato nativamente con l'ecosistema **Firebase**, offre un piano gratuito generosissimo (2 milioni di richieste al mese) ed elimina ogni costo fisso di gestione. 
Grazie a **Cloud Storage FUSE**, possiamo montare un bucket di archiviazione come cartella locale `/data` per conservare i database JSON e i documenti caricati in `/uploads` in modo permanente e sicuro ad ogni riavvio!

### 🛠️ Prerequisiti:
1. Crea un account o accedi a [Google Cloud Console](https://console.cloud.google.com/).
2. Crea un nuovo progetto (es. `la-sorgente-hub`).
3. Associa una carta di credito/debito per abilitare la fatturazione (GCP richiede la verifica dell'identità dell'account, ma i consumi rientreranno al 100% nelle soglie gratuite).

---

### 🖱️ Metodo A: Configurazione Rapida via Interfaccia Web (Nessuna installazione locale)

Questo metodo ti permette di fare tutto dal browser tramite **Google Cloud Shell** (un terminale Linux gratuito e pronto all'uso fornito da Google):

1. **Apri Google Cloud Shell**:
   * Clicca sull'icona del terminale `>_` in alto a destra nella barra di Google Cloud Console.
2. **Carica il Pacchetto**:
   * Clicca sui tre puntini `...` in alto a destra nella finestra di Cloud Shell e seleziona **Upload**.
   * Carica il file `la_sorgente_deploy.zip` generato in precedenza.
3. **Estrai il pacchetto e posizionati nella cartella**:
   ```bash
   unzip la_sorgente_deploy.zip -d la_sorgente
   cd la_sorgente
   ```
4. **Crea il Bucket di Storage per i Dati**:
   * Esegui il comando per creare un bucket per i tuoi dati persistenti (sostituisci `NOME_PROGETTO` col tuo ID progetto Google Cloud):
   ```bash
   gcloud storage buckets create gs://NOME_PROGETTO-dati --location=europe-west9
   ```
5. **Avvia il Build e il Deploy su Cloud Run**:
   * Esegui il comando di deploy automatico compilando l'immagine sul server di Google (sostituisci `NOME_PROGETTO` col tuo ID progetto):
   ```bash
   gcloud run deploy la-sorgente-hub \
     --source . \
     --region europe-west9 \
     --allow-unauthenticated \
     --set-env-vars="GEMINI_API_KEY=LA_TUA_CHIAVE_API,APP_PASSWORD=PASSWORD_SICURA,PERSISTENT_DATA_DIR=/data" \
     --add-volume=name=bucket-dati,type=cloud-storage,bucket=NOME_PROGETTO-dati \
     --add-volume-mount=volume=bucket-dati,mount-path=/data
   ```
   * *Nota: La regione consigliata è `europe-west9` (Parigi) o `europe-west1` (Belgio) per conformità GDPR sui dati in Europa.*
6. **Fatto!**
   * Al termine del deploy, il terminale ti restituirà l'URL pubblico sicuro HTTPS (es. `https://la-sorgente-hub-xxxxxx-ew.a.run.app`). L'applicazione è online e pronta all'uso!

---

### 🖥️ Metodo B: Configurazione tramite gcloud CLI (Terminale Locale)

Se preferisci lavorare dal tuo computer locale con il terminale del Mac:

1. **Installa Google Cloud CLI**:
   * Se non lo hai fatto, installalo seguendo la documentazione ufficiale o usa Homebrew sul Mac:
     ```bash
     brew install --cask google-cloud-sdk
     ```
2. **Inizializza l'ambiente e accedi**:
   ```bash
   gcloud init
   ```
   *(Segui le istruzioni per accedere col tuo account Google ed impostare il progetto predefinito)*
3. **Crea il Bucket**:
   ```bash
   gcloud storage buckets create gs://NOME_DEL_TUO_BUCKET --location=europe-west9
   ```
4. **Deploy del Progetto**:
   * Posizionati nella directory di deploy `la_sorgente_deploy` locale ed esegui:
   ```bash
   gcloud run deploy la-sorgente-hub \
     --source . \
     --region europe-west9 \
     --allow-unauthenticated \
     --set-env-vars="GEMINI_API_KEY=LA_TUA_CHIAVE_API,APP_PASSWORD=PASSWORD_SICURA,PERSISTENT_DATA_DIR=/data" \
     --add-volume=name=bucket-dati,type=cloud-storage,bucket=NOME_DEL_TUO_BUCKET \
     --add-volume-mount=volume=bucket-dati,mount-path=/data
   ```

---

## 🚀 3. Deploy su Render.com (Opzione Cloud Alternativa)

Render.com è una piattaforma PaaS moderna e velocissima. Abbiamo incluso il supporto ai **Blueprint di Render (`render.yaml`)** che configura automaticamente il server e un **disco persistente (SSD)** in un clic.

### Passi per il Deploy Automatico:
1. Crea un repository **privato** su GitHub e inserisci all'interno i file estratti da `la_sorgente_deploy.zip`.
2. Accedi a [Render.com](https://render.com/) e collega il tuo account GitHub.
3. Clicca su **New +** e seleziona **Blueprint**.
4. Scegli il tuo repository privato appena creato.
5. Render rileverà automaticamente il file `render.yaml` e ti chiederà di inserire:
   - `GEMINI_API_KEY`: La chiave API generata da Google AI Studio.
   - `APP_PASSWORD`: La password d'accesso segreta che bloccherà l'applicazione (Password Gate) garantendo che solo le persone autorizzate possano accedere.
6. Clicca su **Apply** ed il deploy si avvierà in modo automatico.

> [!IMPORTANT]
> **Come funziona la persistenza su Render**:
> Il file `render.yaml` alloca un disco fisso da 1 GB montato su `/data`. Tutti i database dei tre moduli (`database.json`, `social_database.json`, `voice_database.json`) ed i documenti caricati in `/uploads` risiederanno lì. Saranno del tutto al sicuro da riavvii, spegnimenti o nuovi deploy dell'applicazione!

---

## 🐳 4. Deploy tramite Docker (Universale)

Se preferisci ospitare l'applicazione su servizi containerizzati (come Fly.io, AWS ECS, DigitalOcean App, ecc.) o sul tuo server locale Docker, abbiamo incluso un `Dockerfile` ottimizzato.

### Comandi per il Build ed Avvio:
1. **Compila l'immagine Docker**:
   ```bash
   docker build -t la-sorgente-hub .
   ```
2. **Avvia il container con i volumi persistenti** (per non perdere i dati):
   ```bash
   docker run -d \
     -p 8081:8081 \
     --name la_sorgente_app \
     -e GEMINI_API_KEY="LA_TUA_CHIAVE_GEMINI" \
     -e APP_PASSWORD="PASSWORD_ACCESSO" \
     -e PERSISTENT_DATA_DIR="/data" \
     -v sorgente_data_volume:/data \
     --restart unless-stopped \
     la-sorgente-hub
   ```

*Nota: Il parametro `-v sorgente_data_volume:/data` mappa i database e la cartella uploads in un volume persistente di Docker sicuro.*

---

## 🖥️ 5. Deploy su VPS Linux Classica (Hetzner, OVH, DigitalOcean, ecc.)

Se utilizzi una macchina VPS con Ubuntu Server (20.04 / 22.04 / 24.04), puoi configurare l'applicazione nativamente con `systemd` e `Nginx` come reverse proxy per avere un indirizzo HTTPS sicuro gratuito.

### Passo 1: Installazione dei prerequisiti sulla VPS
```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx git -y
```

### Passo 2: Copia l'applicazione sulla VPS
Scompatta il file `la_sorgente_deploy.zip` in `/var/www/la_sorgente`:
```bash
sudo mkdir -p /var/www/la_sorgente
# Trasferisci ed estrai i file qui
```

### Passo 3: Configura l'ambiente Python e le dipendenze
```bash
cd /var/www/la_sorgente
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Passo 4: Configura il file `.env` di Produzione
Crea il file `/var/www/la_sorgente/.env` e configuralo così:
```env
GEMINI_API_KEY=inserisci_qui_la_tua_chiave_gemini
APP_PASSWORD=password_segreta_accesso
PERSISTENT_DATA_DIR=/var/www/la_sorgente/data
```
*(Crea la cartella data: `mkdir -p /var/www/la_sorgente/data`)*

### Passo 5: Configura il Servizio Systemd (Avvio in background)
Crea il file `/etc/systemd/system/la_sorgente.service`:
```ini
[Unit]
Description=La Sorgente FastAPI Hub Application
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/la_sorgente
ExecStart=/var/www/la_sorgente/venv/bin/uvicorn app:app --host 127.0.0.1 --port 8081
Restart=always
EnvironmentFile=/var/www/la_sorgente/.env

[Install]
WantedBy=multi-user.target
```

Attiva e avvia il servizio:
```bash
sudo systemctl daemon-reload
sudo systemctl enable la_sorgente
sudo systemctl start la_sorgente
# Verifica lo stato
sudo systemctl status la_sorgente
```

### Passo 6: Configura Nginx come Reverse Proxy e SSL
Crea una configurazione di Nginx `/etc/nginx/sites-available/la_sorgente`:
```nginx
server {
    listen 80;
    server_name iltuodominio.it; # Sostituisci col tuo dominio reale

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Abilita il sito e riavvia Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/la_sorgente /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Ottieni il certificato SSL gratuito tramite Let's Encrypt / Certbot:
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d iltuodominio.it
```

---

## 🔒 6. Raccomandazioni di Sicurezza in Produzione

1. **Password Robusta**: Imposta sempre una `APP_PASSWORD` complessa in produzione per evitare l'utilizzo non autorizzato della chiave API di Gemini.
2. **Chiavi API Personali**: Assicurati che ogni utente/cliente finale utilizzi una propria chiave Gemini API inserita nel proprio pannello o file `.env`.
3. **Backup dei Dati**: Crea un cron job per fare il backup periodico della cartella indicata in `PERSISTENT_DATA_DIR`. Contiene tutti i file modificati dall'utente e i database JSON.

