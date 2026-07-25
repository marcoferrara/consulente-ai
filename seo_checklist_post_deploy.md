# Checklist SEO post-deploy — Aijò Consulente AI

Dominio: **www.aijo-consulenteai.it** · DNS su **Aruba** · Hosting **GitHub Pages**
Da fare dopo il deploy delle pagine SEO (giugno 2026).

---

## 1. Google Search Console (GSC)

Serve a far indicizzare le pagine in fretta e a monitorare le query reali.

### A. Verifica della proprietà
1. Vai su [search.google.com/search-console](https://search.google.com/search-console) e accedi con `marco.ferrara1980@gmail.com`.
2. Aggiungi proprietà → scegli **"Dominio"** (copre http, https, www e non-www in un colpo solo).
3. Google ti dà un record **TXT** da inserire nel DNS.
4. Entra nel **pannello Aruba** → gestione DNS del dominio `aijo-consulenteai.it` → aggiungi un record:
   - Tipo: `TXT`
   - Nome/Host: `@` (oppure vuoto, dipende da Aruba)
   - Valore: `google-site-verification=...` (quello fornito da Google)
5. Salva. La propagazione DNS può richiedere da pochi minuti a qualche ora.
6. Torna su GSC → **Verifica**.

> Alternativa più rapida se il DNS dà problemi: proprietà tipo **"Prefisso URL"** = `https://www.aijo-consulenteai.it/`, verifica con file HTML caricato nella root del repo (si committa come le altre pagine). Ma la proprietà "Dominio" è preferibile.

### B. Invio della sitemap
1. In GSC → menu **Sitemap**.
2. Inserisci: `sitemap.xml` → Invia.
3. Controlla dopo 1-2 giorni che risulti **"Riuscito"** con 7 URL letti.

### C. Forza l'indicizzazione delle pagine nuove
Per ognuna di queste, usa **Controllo URL** (barra in alto) → incolla l'URL → **Richiedi indicizzazione**:
- [ ] https://www.aijo-consulenteai.it/
- [ ] https://www.aijo-consulenteai.it/integrare-intelligenza-artificiale-azienda/
- [ ] https://www.aijo-consulenteai.it/intelligenza-artificiale-cagliari/
- [ ] https://www.aijo-consulenteai.it/intelligenza-artificiale-sassari/
- [ ] https://www.aijo-consulenteai.it/intelligenza-artificiale-olbia/
- [ ] https://www.aijo-consulenteai.it/intelligenza-artificiale-oristano/
- [ ] https://www.aijo-consulenteai.it/intelligenza-artificiale-nuoro/

### D. Controlli tecnici (una tantum)
- [ ] **Test dei risultati avanzati** ([search.google.com/test/rich-results](https://search.google.com/test/rich-results)): incolla una pagina città → deve rilevare **FAQ** e **Breadcrumb** validi.
- [ ] **robots.txt**: apri https://www.aijo-consulenteai.it/robots.txt → deve mostrare la riga `Sitemap:`.
- [ ] Verifica che le pagine NON abbiano header `noindex` (GitHub Pages produzione non lo mette; le anteprime sì).

### E. Monitoraggio (ricorrente, ogni 2-4 settimane)
- [ ] **Rendimento** → filtra per query: cerca `cagliari`, `integrare`, `sassari`...
- [ ] Le query con **posizione media 8-20** sono le opportunità: lì conviene aggiungere contenuto/FAQ alla pagina relativa.
- [ ] **Pagine** → controlla che le 7 URL siano "Indicizzate".

---

## 2. Google Business Profile (GBP)

È ciò che ti fa comparire nel **riquadro mappa** ("local pack") e su Google Maps per ricerche tipo *consulente ai cagliari*. Fondamentale per la local SEO.

### A. Creazione / rivendicazione
1. Vai su [business.google.com](https://business.google.com) con `marco.ferrara1980@gmail.com`.
2. Nome attività: **Aijò — Consulente AI** (coerente col brand, senza nome e cognome).
3. Categoria principale: **"Consulente"** (o "Servizio di consulenza aziendale" / "Consulente informatico"). Aggiungi categorie secondarie pertinenti.

### B. Tipo di attività: "area di servizio" (IMPORTANTE)
Non avendo un negozio fisico aperto al pubblico:
1. Alla domanda sull'indirizzo → scegli **"Consegno beni e servizi ai clienti"** / attività **senza sede visitabile**.
2. **Nascondi l'indirizzo** e imposta le **aree servite**:
   - [ ] Cagliari · [ ] Sassari · [ ] Olbia · [ ] Oristano · [ ] Nuoro · [ ] Sardegna
3. Così appari nelle ricerche locali senza esporre un indirizzo di casa.

### C. Completa il profilo al 100%
- [ ] **Telefono** (numero su cui rispondi davvero)
- [ ] **Sito web**: `https://www.aijo-consulenteai.it/`
- [ ] **Orari**: Lun-Ven 09:00-18:00 (coerenti con lo schema del sito)
- [ ] **Descrizione**: usa le keyword — "integrare l'intelligenza artificiale", "consulente AI in Sardegna", "PMI", città.
- [ ] **Logo** (`logo_aijo_definitivo.png`) + qualche foto/immagine (anche grafiche del brand)
- [ ] **Servizi**: aggiungi voci come "Strategia e Roadmap AI", "Implementazione AI", "Formazione del team", "AI per marketing e dati"

### D. Verifica
- Google chiede di verificare l'attività (cartolina, telefono, video o email a seconda dei casi). Completa la procedura: finché non sei verificato, la scheda non compare.

### E. Attività continua (alza il ranking locale)
- [ ] Pubblica un **Post** ogni 1-2 settimane (novità, casi, consigli AI per imprese sarde)
- [ ] Chiedi **recensioni** ai clienti soddisfatti (il fattore #1 del local ranking)
- [ ] Rispondi a TUTTE le recensioni
- [ ] Tieni link sito + telefono sempre aggiornati

---

## 3. Bonus consigliati
- [ ] **Bing Webmaster Tools**: importa direttamente la proprietà da GSC (2 minuti, copri anche Bing/ChatGPT search).
- [ ] **Coerenza NAP** (Name-Address-Phone): usa sempre la stessa dicitura "Aijò — Consulente AI" + stesso telefono ovunque (sito, GBP, LinkedIn, directory).
- [ ] **LinkedIn**: pagina/profilo collegato; aggiungilo come `sameAs` nello schema del sito quando ce l'hai.

---

### Priorità (se hai poco tempo)
1. GSC: verifica dominio + invio sitemap + richiesta indicizzazione → **subito**
2. GBP: crea scheda area-servizio + verifica → **questa settimana**
3. Recensioni + monitoraggio GSC → **continuo**
