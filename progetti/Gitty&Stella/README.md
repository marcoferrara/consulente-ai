# Gitty&Stella — Prototipo landing page + assistente WhatsApp

Prototipo di landing page multilingua (IT/EN/DE/FR) e backend AI per un appartamento in affitto breve in **Via Sardegna, Oristano**.

Il sistema implementa:
1. **Landing page ad alta conversione** (`index.html`): hero, value proposition, galleria, descrizione, servizi, zona, sezione "prova sociale" onesta (nessuna recensione finta), FAQ con JSON-LD, footer.
2. **Switch lingua vanilla JS** (`i18n.js`): 4 lingue, persistenza in `localStorage`, fallback su lingua del browser.
3. **Assistente AI via webhook WhatsApp** (`app.py`): risponde a domande su disponibilità/prezzo, raccoglie richieste di prenotazione e **notifica il proprietario** (mock). Nessuna prenotazione è mai confermata automaticamente: resta sempre una richiesta in attesa di conferma del proprietario.
4. **Fallback senza chiave API**: se non è configurata una chiave OpenAI/Gemini valida, il bot risponde comunque con un motore mock multilingua (`process_mock_response`), utile per demo senza credenziali.

## Struttura progetto

```
app.py            # Server FastAPI + orchestratore AI (function calling)
config.py         # Dati appartamento, date mock già occupate, chiavi API
requirements.txt  # Dipendenze
index.html        # Landing page + widget chat demo stile WhatsApp
i18n.js           # Traduzioni IT/EN/DE/FR + logica di switch lingua
test_client.py    # Script di test conversazionale da riga di comando
static/images/    # Foto stock PLACEHOLDER — vedi checklist sotto
```

## Come avviarlo

> Nota: la cartella del progetto si chiama `Gitty&Stella` (con l'e commerciale). Ricorda di quotare il percorso nei comandi da terminale.

```bash
cd "progetti/Gitty&Stella"
pip install -r requirements.txt
```

Imposta (facoltativo) una chiave API per usare un vero LLM invece del motore mock:

```bash
export GEMINI_API_KEY="la-tua-chiave-gemini"
# oppure
export OPENAI_API_KEY="la-tua-chiave-openai"
```

Avvia il server:

```bash
uvicorn app:app --reload --port 8010
```

Apri `http://localhost:8010/` per vedere la landing page con il widget di chat collegato dal vivo al backend.

Per un test conversazionale da terminale:

```bash
python test_client.py
```

## Endpoint principali

- `GET /` — landing page
- `POST /webhook/whatsapp` — riceve `{user_id, message, user_name}`, simula il webhook WhatsApp
- `GET /api/apartment` — dati statici dell'appartamento
- `GET /api/booking-requests` — richieste di prenotazione in attesa di conferma
- `GET /api/owner/notifications` — notifiche mock inviate al proprietario (mini "owner dashboard")
- `POST /api/reset` — azzera lo stato della demo (utile prima di ogni presentazione al cliente)

## Checklist prima del lancio pubblico

Cercare `PLACEHOLDER` e `data-placeholder="true"` nel codice per trovare rapidamente tutti i contenuti da confermare:

- [ ] Sostituire le foto in `static/images/` con scatti reali dell'appartamento
- [ ] Confermare mq, numero camere/bagni, ospiti massimi, dotazioni reali
- [ ] Confermare prezzo per notte, sconto soggiorni lunghi, cauzione/pulizie
- [ ] Numero WhatsApp reale (sostituire `+390000000000` in `index.html`)
- [ ] Contatti e dati fiscali reali nel footer
- [ ] Collegare un calendario reale (es. Google Calendar) invece di `MOCK_BOOKED_RANGES` in `config.py`
- [ ] Attivare un canale di notifica reale per il proprietario (WhatsApp/email) invece del log mock
- [ ] Valutare integrazione reale WhatsApp Business API (Meta Cloud API o Twilio) — richiede account Business verificato

## Roadmap futura (fuori scope di questo prototipo)

- Integrazione reale WhatsApp Business API
- Sincronizzazione con Google Calendar per la disponibilità reale
- Recensioni reali con relativo `AggregateRating` nello structured data
- Pagine SEO satellite dedicate, se il progetto crescerà a più immobili
