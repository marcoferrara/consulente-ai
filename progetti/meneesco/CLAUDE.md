# Meneesco — CLAUDE.md

## Progetto
Landing page istituzionale con backend FastAPI per il "Metodo Meneesco". Raccoglie richieste istituzionali in `leads.json`. Include asset di presentazione (PDF, DOCX, logo).

## Stack
- **Landing:** HTML/CSS/JS statico in un solo file (`index.html`, tema crema/crimson, font Cormorant)
- **Form:** Web3Forms (no backend) — la access key è del cliente
- **Analytics:** Google Analytics 4 con cookie banner a consenso (GA caricato solo dopo "Accetta")
- **Backend (separato):** `app.py` FastAPI è un prodotto distinto ("bandi"), NON serve la landing

## Deliverable / deploy
La landing è un **progetto standalone da consegnare al cliente**: va nel **GitHub del cliente** e sul **suo dominio**. La cartella `meneesco/` è pensata come root del sito del cliente.

### Placeholder da compilare prima della messa online
- **Dominio:** ovunque è usato `https://www.meneesco.it/` (canonical, OG, JSON-LD, `sitemap.xml`, `robots.txt`)
- **GA4:** `GA_ID = 'G-XXXXXXXXXX'` nello script in fondo a `index.html`
- **Web3Forms:** `access_key: 'INSERIRE-ACCESS-KEY-WEB3FORMS-CLIENTE'` in `index.html` (mail di destinazione del cliente)
- **Dati legali:** `[RAGIONE SOCIALE]`, `[P.IVA]`, `[INDIRIZZO]`, `[EMAIL CLIENTE]` in `privacy.html`

## Struttura
```
index.html      # Landing page (unica) + FAQ + cookie banner + GA4
privacy.html    # Informativa privacy (GDPR)
cookie.html     # Cookie policy + reset consenso
robots.txt      # Standalone (dominio cliente)
sitemap.xml     # Standalone (home + privacy + cookie)
app.py          # FastAPI prodotto "bandi" (separato dalla landing)
Manuale Meneesco finale .pdf
Presentazione MENEESCO.docx
```

## Note
- Esiste un solo `index.html` (la vecchia `index_v2.html` è stata rinominata; la v1 eliminata)
- SEO: keyword P.A./de-escalation integrate nei testi; FAQ con schema `FAQPage`; JSON-LD Organization + Course

## Convenzioni
- Commenti in italiano su ogni funzione
- Indentazione 4 spazi (PEP8)
- Conventional commits in italiano
