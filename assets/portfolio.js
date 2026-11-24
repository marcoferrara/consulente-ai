/* ===========================================================================
   Aijò — Pagina Portfolio: console prototipi,
   filtri archivio. JavaScript vanilla, nessuna dipendenza.
   =========================================================================== */
(function () {
  'use strict';

  /* ── DATI DEI PROTOTIPI ───────────────────────────────────────────────── */
  // I valori di impatto sono stime di progetto, non misure: la pagina lo dichiara.
  var SIM = {
    turismo: {
      badge: 'Turismo & Hospitality',
      challenge: 'Da aprile a settembre riceviamo centinaia di richieste al giorno via email e WhatsApp: transfer, intolleranze, escursioni, cene tipiche. Chi sta alla reception è sopraffatto, risponde in ritardo e perdiamo prenotazioni dirette a favore dei portali.',
      solution: 'Un concierge AI multilingua su WhatsApp e sito web. Conosce le guide del territorio e i listini dell\'hotel e dialoga con il gestionale per proporre disponibilità e preventivi in tempo reale.',
      tech: ['Personalizzazione LLM', 'Integrazione gestionale', 'WhatsApp Business', 'NLP multilingua'],
      i1: ['+25%', 'Prenotazioni dirette'],
      i2: ['4 ore/giorno', 'Tempo risparmiato allo staff'],
      cta: null // nessuna demo pubblica per questo caso
    },
    export: {
      badge: 'Agroalimentare & Export',
      challenge: 'Vogliamo vendere all\'estero ma non abbiamo un reparto marketing internazionale. Dobbiamo adattare le schede tecniche, scrivere newsletter per gli importatori e capire cosa si dice di noi nelle recensioni straniere.',
      solution: 'Una pipeline di contenuti e analisi del sentiment. L\'AI non traduce alla lettera: adatta il racconto al mercato (ad esempio la longevità del vino per il pubblico americano) ed estrae insight dalle recensioni estere.',
      tech: ['Localizzazione AI', 'Tono di voce del brand', 'Sentiment analysis', 'Market intelligence'],
      i1: ['3 canali', 'Nuovi mercati aperti'],
      i2: ['-90%', 'Costo di localizzazione'],
      cta: { type: 'link', href: '/demo/cantina_vinicola/index.html', label: 'Apri la demo 🍷' }
    },
    rag: {
      badge: 'Servizi professionali',
      challenge: 'Passiamo decine di ore alla settimana a scorrere i bandi regionali per capire quali dei nostri oltre 300 clienti hanno i requisiti per un finanziamento. Spesso ci sfuggono scadenze o bandi minori.',
      solution: 'Una knowledge base privata con ricerca semantica (RAG): si caricano bandi, delibere e normative e i professionisti interrogano il sistema in linguaggio naturale, incrociando subito i profili aziendali.',
      tech: ['Architettura RAG', 'Database vettoriale', 'Ricerca semantica', 'Indicizzazione documenti'],
      i1: ['80%', 'Tempo di ricerca risparmiato'],
      i2: ['Zero', 'Scadenze perse'],
      cta: { type: 'link', href: '/demo/studio_associato/index.html', label: 'Apri la demo 🔍' }
    },
    artigianato: {
      badge: 'Artigianato & e-commerce',
      challenge: 'Realizziamo pezzi unici di grande valore ma non riusciamo a venderli online: scrivere descrizioni accurate, ottimizzate per i motori di ricerca e in più lingue, per ogni pezzo, ci porta via troppo tempo.',
      solution: 'Un sistema multimodale da immagine a testo. L\'artigiano fotografa il pezzo, l\'AI ne riconosce trama e simboli e genera descrizioni emozionali e tradotte, collegate a un assistente per le spedizioni.',
      tech: ['Visione multimodale', 'Copywriting SEO', 'API e-commerce', 'Riconoscimento visivo'],
      i1: ['30 min → 2', 'Inserimento di un prodotto'],
      i2: ['+40%', 'Conversioni estero'],
      cta: { type: 'link', href: '/demo/laboratorio_artistico/index.html', label: 'Apri la demo 🎨' }
    },
    logistica: {
      badge: 'Logistica & distribuzione',
      challenge: 'Consegniamo in tutta l\'isola, anche nei piccoli centri dell\'interno. Strade tortuose, orari dei negozi e carburante erodono i margini: dobbiamo ottimizzare carichi e consegne.',
      solution: 'Un sistema predittivo per scorte e percorsi, con machine learning leggero. Incrocia meteo, festività locali e storico ordini per anticipare la domanda ed evitare consegne a vuoto.',
      tech: ['Analisi predittiva', 'Ottimizzazione percorsi', 'Previsione scorte', 'Machine learning'],
      i1: ['15%', 'Risparmio carburante'],
      i2: ['-90%', 'Consegne mancate e fuori scorta'],
      cta: { type: 'link', href: '/demo/logistica/index.html', label: 'Apri la demo 🚚' }
    }
  };

  /* ── RIFERIMENTI DOM ──────────────────────────────────────────────────── */
  var $ = function (id) { return document.getElementById(id); };
  var tabs = Array.prototype.slice.call(document.querySelectorAll('.pf-tab'));
  var screens = { challenge: $('scr-challenge'), solution: $('scr-solution') };
  var dot = $('pf-dot'), statusEl = $('pf-status'), badge = $('pf-badge'), scan = $('pf-scan');
  var btnSolve = $('btn-solve');
  var current = 'turismo';
  var busy = false;
  var timers = [];

  // Pulisce eventuali timer pendenti (cambio scheda durante l'animazione)
  function clearTimers() {
    timers.forEach(clearTimeout);
    timers = [];
  }

  // Mostra una sola schermata della console
  function show(name) {
    Object.keys(screens).forEach(function (k) {
      screens[k].classList.toggle('show', k === name);
    });
  }

  // Imposta stato e indicatore luminoso dell'intestazione
  function setStatus(text, on) {
    statusEl.textContent = text;
    dot.classList.toggle('on', !!on);
  }

  /* ── CONSOLE: SCHEDE SETTORE ──────────────────────────────────────────── */
  // Seleziona un settore e riporta la console alla schermata iniziale
  function selectSim(key, focus) {
    clearTimers();
    busy = false;
    scan.classList.remove('go');
    btnSolve.disabled = false;
    btnSolve.textContent = 'Risolvi con l\'AI →';
    current = key;
    var d = SIM[key];
    badge.textContent = d.badge;
    $('txt-challenge').textContent = d.challenge;
    setStatus('In attesa', false);
    show('challenge');
    tabs.forEach(function (t) {
      var on = t.dataset.sim === key;
      t.setAttribute('aria-selected', on ? 'true' : 'false');
      t.tabIndex = on ? 0 : -1;
      if (on && focus) t.focus();
    });
  }

  tabs.forEach(function (t, i) {
    t.addEventListener('click', function () { selectSim(t.dataset.sim, false); });
    // Navigazione da tastiera tra le schede (frecce, Home, Fine)
    t.addEventListener('keydown', function (e) {
      var n = tabs.length, next = null;
      if (e.key === 'ArrowDown' || e.key === 'ArrowRight') next = (i + 1) % n;
      if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') next = (i - 1 + n) % n;
      if (e.key === 'Home') next = 0;
      if (e.key === 'End') next = n - 1;
      if (next !== null) { e.preventDefault(); selectSim(tabs[next].dataset.sim, true); }
    });
  });

  // "Risolvi con l'AI": animazione di scansione e poi la soluzione
  btnSolve.addEventListener('click', function () {
    if (busy) return;
    busy = true;
    var d = SIM[current];
    scan.classList.remove('go');
    void scan.offsetWidth; // riavvia l'animazione
    scan.classList.add('go');
    setStatus('Elaborazione in corso…', false);
    btnSolve.disabled = true;
    btnSolve.textContent = 'Elaborazione…';

    timers.push(setTimeout(function () {
      $('txt-solution').textContent = d.solution;
      $('chips').innerHTML = d.tech.map(function (t) { return '<span>' + t + '</span>'; }).join('');
      $('imp1-v').textContent = d.i1[0];
      $('imp1-l').textContent = d.i1[1];
      $('imp2-v').textContent = d.i2[0];
      $('imp2-l').textContent = d.i2[1];

      // Pulsante della demo: solo per i casi che ne hanno una
      var slot = $('demo-slot');
      slot.innerHTML = '';
      if (d.cta) {
        var a = document.createElement('a');
        a.className = 'pf-btn';
        a.href = d.cta.href;
        a.target = '_blank';
        a.rel = 'noopener';
        a.textContent = d.cta.label;
        slot.appendChild(a);
      }

      show('solution');
      setStatus('Flusso AI attivo', true);
      btnSolve.disabled = false;
      btnSolve.textContent = 'Risolvi con l\'AI →';
      busy = false;
    }, 1500));
  });

  $('btn-back').addEventListener('click', function () { selectSim(current, false); });

  /* ── ARCHIVIO: FILTRI E CONTEGGI ──────────────────────────────────────── */
  var cards = Array.prototype.slice.call(document.querySelectorAll('#pf-grid .pf-card'));
  var filters = Array.prototype.slice.call(document.querySelectorAll('.pf-filter'));

  filters.forEach(function (f) {
    f.addEventListener('click', function () {
      var key = f.dataset.filter;
      filters.forEach(function (x) { x.setAttribute('aria-pressed', x === f ? 'true' : 'false'); });
      cards.forEach(function (c) { c.hidden = !(key === 'all' || c.dataset.cat === key); });
    });
  });

  // Numeri in testata calcolati dalle schede (+ i 5 settori delle demo)
  var settori = {};
  cards.forEach(function (c) { settori[c.dataset.sector] = 1; });
  ['Agroalimentare', 'Servizi', 'Artigianato', 'Logistica', 'Turismo'].forEach(function (s) { settori[s] = 1; });
  $('stat-progetti').textContent = String(cards.length + 5);
  $('stat-settori').textContent = String(Object.keys(settori).length);

  // Avvio: scheda iniziale
  selectSim('turismo', false);
})();
