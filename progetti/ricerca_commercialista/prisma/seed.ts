import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function main() {
  console.log("Seeding started...");

  // 1. Clean existing records
  await prisma.searchLog.deleteMany({});
  await prisma.erpMapping.deleteMany({});
  await prisma.accountingProcedure.deleteMany({});
  await prisma.user.deleteMany({});
  await prisma.firm.deleteMany({});

  // 2. Create default Firm
  const firm = await prisma.firm.create({
    data: {
      name: "Studio Associato Tributario Rossi & Bianchi",
      vatNumber: "01234567890",
      subscriptionPlan: "PROFESSIONAL",
    },
  });

  // 3. Create default User (Commercialista)
  const user = await prisma.user.create({
    data: {
      name: "Mario Rossi",
      email: "mario.rossi@studiorossi.it",
      passwordHash: "demo1234", // mock plain password hash
      role: "ADMIN",
      firmId: firm.id,
    },
  });

  console.log("Created default firm and user:", firm.name, user.email);

  // 4. Create Accounting Procedures and their ERP Mappings

  // Procedure 1: Autofattura TD17 per servizi da Paese UE
  const proc1 = await prisma.accountingProcedure.create({
    data: {
      title: "Autofattura TD17 per servizi da Paese UE",
      normativeSummary: "In caso di acquisto di servizi da un fornitore stabilito in un altro paese dell'Unione Europea, il cliente italiano (soggetto passivo IVA) deve integrare la fattura ricevuta o emettere un'autofattura con codice tipo documento TD17, applicando l'aliquota IVA italiana tramite il meccanismo del reverse charge entro il giorno 15 del mese successivo.",
      electronicInvoicingFields: {
        tipo_documento: "TD17",
        natura_iva: "N6.9",
        descrizione: "Integrazione/Autofattura per acquisto servizi dall'estero",
      },
      officialSources: [
        {
          source_name: "Agenzia delle Entrate - Guida alla compilazione delle fatture elettroniche",
          url: "https://www.agenziaentrate.gov.it/portale/documents/20143/288640/Guida_compilazione_FE_v1.8.pdf",
          target_paragraph: "Sezione 3.17 - Tipo Documento TD17",
        },
        {
          source_name: "D.P.R. 633/1972 - Articolo 17, comma 2",
          url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633~art17",
          target_paragraph: "Articolo 17, comma 2 - Soggetti passivi",
        },
      ],
      // Contenuto estratto dalle fonti ufficiali per la Citations API di Anthropic
      sourceContents: [
        {
          source_name: "Agenzia delle Entrate - Guida alla compilazione delle fatture elettroniche",
          url: "https://www.agenziaentrate.gov.it/portale/documents/20143/288640/Guida_compilazione_FE_v1.8.pdf",
          content: "TIPO DOCUMENTO TD17 – Integrazione/Autofattura per acquisto servizi dall'estero\n\nIl tipo documento TD17 viene utilizzato dal cessionario/committente italiano soggetto passivo IVA per integrare o autofatturare l'acquisto di servizi da fornitori esteri (sia UE che extra-UE). Il meccanismo applicato è quello del reverse charge (inversione contabile), ai sensi dell'art. 17, comma 2, del D.P.R. 633/1972.\n\nIl documento deve essere emesso entro il giorno 15 del mese successivo a quello di effettuazione dell'operazione. L'IVA italiana deve essere applicata all'aliquota ordinaria corrispondente al servizio acquistato (es. 22% per servizi generici). Il documento va trasmesso allo SDI con codice destinatario del cedente estero pari a 'XXXXXXX'. La natura IVA da indicare è N6.9 per le operazioni in regime di reverse charge non codificate altrimenti.",
        },
        {
          source_name: "D.P.R. 633/1972 - Articolo 17, comma 2",
          url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633~art17",
          content: "Art. 17 D.P.R. 633/1972 - Soggetti passivi\n\nComma 2: Gli obblighi relativi alle cessioni di beni e alle prestazioni di servizi effettuate nel territorio dello Stato da soggetti non residenti nei confronti di soggetti passivi stabiliti nel territorio dello Stato, compresi i soggetti indicati all'articolo 7-ter, comma 2, lettere b) e c), sono adempiuti dai cessionari o committenti. Tali soggetti assolvono l'imposta mediante il meccanismo dell'inversione contabile (reverse charge), registrando il documento sia nel registro IVA acquisti che nel registro IVA vendite, con effetto neutro ai fini della detrazione.",
        },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc1.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Accedere al modulo Contabilità > Prima Nota > Registrazioni.",
          "Creare una nuova registrazione con causale 'FAEU - Fattura Acquisto Servizi UE'.",
          "Inserire i dati del fornitore UE con aliquota IVA corrispondente (es. 22% ordinaria).",
          "Il sistema genererà automaticamente una seconda registrazione di integrazione vendite.",
          "Nel pannello Fatturazione Elettronica, selezionare Tipo Documento 'TD17' e avviare l'invio allo SDI.",
        ],
        notes: "Assicurarsi che l'anagrafica del fornitore contenga il codice nazione corretto e l'ID IVA comunitario validato su VIES.",
      },
      {
        procedureId: proc1.id,
        erpName: "TeamSystem",
        stepByStepGuide: [
          "Selezionare il menu Contabilità > Prima Nota > Inserimento Movimenti.",
          "Utilizzare la causale contabile 'AUE' (Acquisti Servizi CEE) che attiva il doppio registro IVA.",
          "Registrare la fattura inserendo l'imponibile; l'IVA verrà calcolata e annotata sia sul registro acquisti che vendite.",
          "Accedere alla console 'Fatturazione Elettronica' per controllare il documento generato automaticamente.",
          "Confermare la generazione del file XML con codice TD17 e firmare digitalmente se richiesto prima dell'invio.",
        ],
        notes: "Controllare che i parametri della causale contabile 'AUE' abbiano il flag 'Reverse Charge CEE' attivo.",
      },
      {
        procedureId: proc1.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Andare nella sezione Acquisti e cliccare su 'Nuovo'.",
          "Selezionare il fornitore UE e spuntare la casella 'Reverse charge (inversione contabile)'.",
          "Impostare l'aliquota IVA standard (es. 22%) e verificare che il totale fattura coincida.",
          "Andare in Strumenti > Invio fatture elettroniche.",
          "Selezionare il documento d'acquisto inserito e generare l'autofattura con codice 'TD17'.",
        ],
        notes: "La natura IVA associata all'autofattura viene gestita in automatico dal software in base alle impostazioni di reverse charge.",
      },
    ],
  });

  // Procedure 2: Reverse Charge interno ex art.17 (Edilizia/Subappalto)
  const proc2 = await prisma.accountingProcedure.create({
    data: {
      title: "Reverse Charge interno ex art. 17 (Edilizia/Subappalto)",
      normativeSummary: "Per le prestazioni di servizi di subappalto nel settore edile, l'IVA è dovuta dal committente (soggetto passivo) anziché dal prestatore. Il prestatore emette fattura senza addebito d'imposta con codice natura N6.3. Il committente deve integrare la fattura con l'aliquota di riferimento ed emettere un'autofattura TD16 per trasmettere l'integrazione allo SDI.",
      electronicInvoicingFields: {
        tipo_documento: "TD16",
        natura_iva: "N6.3",
        descrizione: "Inversione contabile - subappalto in edilizia",
      },
      officialSources: [
        {
          source_name: "Agenzia delle Entrate - Circolare 14/E del 2015",
          url: "https://www.agenziaentrate.gov.it/portale/documents/20143/305929/Circolare_14_E_del_27_03_2015.pdf",
          target_paragraph: "Paragrafo 2 - Subappalto nel settore edile",
        },
        {
          source_name: "D.P.R. 633/1972 - Articolo 17, comma 6, lett. a)",
          url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633~art17",
          target_paragraph: "Articolo 17, comma 6, lettera a) - Reverse charge in edilizia",
        },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc2.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Aprire la schermata di registrazione Prima Nota.",
          "Usare causale 'REV_ED' (Reverse Charge Edilizia).",
          "Registrare la fattura fornitore indicando l'esenzione con codice IVA corrispondente all'Art.17 c.6 lett. a (N6.3).",
          "Il sistema effettua l'autointegrazione sui registri IVA vendite e acquisti.",
          "Generare l'autofattura integrativa con codice 'TD16' e inviarla allo SDI tramite il modulo Digital Hub Zucchetti.",
        ],
        notes: "Il codice IVA deve essere mappato correttamente con il codice natura N6.3 nelle tabelle di base.",
      },
      {
        procedureId: proc2.id,
        erpName: "TeamSystem",
        stepByStepGuide: [
          "Inserire un nuovo movimento di Prima Nota.",
          "Selezionare causale 'RCE' (Reverse Charge Edilizia Subappalto).",
          "Inserire il conto di costo e l'aliquota di esenzione/inversione agganciata a N6.3.",
          "Il programma rileverà automaticamente la necessità di generare un'autofattura TD16.",
          "Verificare la corretta registrazione nei registri IVA acquisti e vendite e procedere all'invio telematico.",
        ],
        notes: "Nel piano dei conti, verificare che il conto di costo utilizzato sia configurato per il reverse charge.",
      },
    ],
  });

  // Procedure 3: Registrazione Forfettario con bollo virtuale
  const proc3 = await prisma.accountingProcedure.create({
    data: {
      title: "Registrazione Forfettario con bollo virtuale",
      normativeSummary: "I contribuenti in regime forfettario sono esenti da IVA (art. 1 comma 58 L. 190/2014) ed emettono fatture con natura IVA N2.2. Se l'importo della fattura supera i 77,47 €, è obbligatorio applicare l'imposta di bollo di 2,00 €. L'indicazione del bollo deve avvenire inserendo il flag di bollo virtuale ('SI') nel tracciato XML della fattura elettronica.",
      electronicInvoicingFields: {
        tipo_documento: "TD01",
        natura_iva: "N2.2",
        bollo_virtuale: "SI",
        importo_bollo: "2.00",
        descrizione: "Non soggette - altri casi (Regime forfettario)",
      },
      officialSources: [
        {
          source_name: "Legge 190/2014 - Regime Forfettario",
          url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:legge:2014-12-23;190",
          target_paragraph: "Articolo 1, commi 54-89",
        },
        {
          source_name: "Agenzia delle Entrate - Risoluzione 428/E del 2008",
          url: "https://www.agenziaentrate.gov.it/portale/documents/20143/339487/ris+428e+del+10+novembre+2008.pdf",
          target_paragraph: "Imposta di bollo su documenti informatici ed esenti IVA",
        },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc3.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Creare una nuova fattura di vendita per il cliente.",
          "Selezionare l'aliquota IVA specifica per il regime forfettario (es. 'Forfettario 0% - N2.2').",
          "Se l'imponibile è superiore a 77,47 €, spuntare la casella 'Applica bollo' nella scheda del documento.",
          "Verificare che l'opzione 'Bollo a carico del cliente' o 'Bollo a carico del mittente' sia configurata correttamente.",
          "Esportare il file XML per l'invio allo SDI: il tag <DatiBollo> conterrà <BolloVirtuale>SI</BolloVirtuale> e <ImportoBollo>2.00</ImportoBollo>.",
        ],
        notes: "Nel pannello delle opzioni generali del registro vendite, definire se il bollo di 2 € deve essere sommato al totale a pagare o registrato como costo.",
      },
    ],
  });

  // Procedure 4: Fatturazione a soggetto in Zona Franca / ZES
  const proc4 = await prisma.accountingProcedure.create({
    data: {
      title: "Fattura a soggetto in Zona Franca / ZES (Lettera d'Intento)",
      normativeSummary: "I soggetti che operano in Zone Economiche Speciali (ZES), porti franchi o depositi doganali possono ricevere forniture in sospensione d'imposta presentando una lettera d'intento al fornitore. La fattura va emessa senza IVA con natura N3.4 ('Non imponibile – esportatori abituali') e deve riportare gli estremi della lettera d'intento ricevuta e la dicitura: 'Operazione non imponibile ex art. 8 c.1 lett. c DPR 633/72'.",
      electronicInvoicingFields: {
        tipo_documento: "TD01",
        natura_iva: "N3.4",
        descrizione: "Non imponibile – esportatori abituali / lettera d'intento (art. 8 c.1 lett. c DPR 633/72)",
      },
      officialSources: [
        {
          source_name: "DPR 633/1972 – Art. 8 c.1 lett. c (Esportatori abituali)",
          url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633~art8",
          target_paragraph: "Art. 8, comma 1, lettera c – Cessioni a esportatori abituali con lettera d'intento",
        },
        {
          source_name: "Agenzia delle Entrate – Dichiarazione d'intento: guida operativa",
          url: "https://www.agenziaentrate.gov.it/portale/web/guest/dichiarazione-d-intento",
          target_paragraph: "Procedura di rilascio e ricezione della dichiarazione d'intento tramite portale AdE",
        },
        {
          source_name: "DL 331/1993 – Art. 50-bis (Depositi IVA)",
          url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legge:1993-08-30;331~art50bis",
          target_paragraph: "Art. 50-bis – Regime di sospensione IVA per depositi doganali e fiscali",
        },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc4.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Ricevere il numero di protocollo AdE della lettera d'intento trasmessa dal cliente.",
          "⭐ BEST PRACTICE per cliente ricorrente — aprire l'anagrafica: Clienti → selezionare il cliente → scheda Dati Fiscali (o Dati Generali). Nel campo 'Aliquota IVA predefinita' selezionare il codice N3.4 – Non imponibile esportatori abituali. Salvare: da questo momento OGNI riga di OGNI nuova fattura per questo cliente userà N3.4 automaticamente senza intervento manuale.",
          "Nelle note dell'anagrafica cliente annotare: protocollo AdE, data lettera d'intento e importo plafond disponibile (es. 'L.I. n. 123456/2024 del 01/01/2024 – plafond €50.000').",
          "Emettere la nuova fattura normalmente: Fatture di Vendita → Nuova Fattura. Le righe prodotto avranno già N3.4 preimpostato dall'anagrafica — non è necessario impostare l'IVA riga per riga.",
          "Aggiungere UNA sola riga di tipo Descrizione con il testo: 'Operazione non imponibile ex art. 8 c.1 lett. c DPR 633/72 – Lettera d'intento n. [PROTOCOLLO AdE] del [DATA]'.",
          "Verificare nell'XML che il tag <Natura> riporti N3.4 su tutte le righe merce.",
          "Inviare allo SDI. Aggiornare il saldo plafond consumato nelle note dell'anagrafica cliente dopo ogni fattura emessa.",
          "ALTERNATIVA per cliente occasionale (una tantum): applicare N3.4 manualmente riga per riga senza modificare l'anagrafica.",
        ],
        notes: "Configurare l'esenzione N3.4 sull'anagrafica cliente evita errori di dimenticanza su singole righe. Ricordarsi di RIMUOVERE l'esenzione dall'anagrafica quando la lettera d'intento scade o il plafond si esaurisce, altrimenti le fatture successive userebbero ancora N3.4 senza diritto. Verificare mensilmente il plafond residuo.",
      },
      {
        procedureId: proc4.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Acquisire il numero di protocollo AdE della lettera d'intento trasmessa dal cliente.",
          "Accedere a Contabilità → Fatturazione Attiva → Nuova Fattura.",
          "Nell'anagrafica cliente verificare che sia attiva la flag 'Esportatore abituale' e che sia inserito il plafond disponibile aggiornato.",
          "Selezionare il codice IVA corrispondente all'art. 8 c.1 lett. c (natura N3.4) nel listino prezzi o direttamente sulla riga.",
          "Nel campo 'Riferimento normativo' della riga IVA, inserire: 'Art. 8 c.1 lett. c DPR 633/72 – L.I. n. [PROTOCOLLO] del [DATA]'.",
          "Dal modulo Digital Hub Zucchetti, generare e verificare l'XML prima dell'invio allo SDI.",
        ],
        notes: "In Zucchetti è possibile configurare un automatismo che stampa gli estremi della lettera d'intento nel piè di pagina di tutte le fatture emesse verso quel cliente.",
      },
      {
        procedureId: proc4.id,
        erpName: "TeamSystem",
        stepByStepGuide: [
          "Registrare la lettera d'intento ricevuta in Contabilità → Archivi → Lettere d'intento, associandola all'anagrafica del cliente.",
          "Creare la fattura di vendita: il sistema proporrà automaticamente il codice di esenzione N3.4 se la lettera d'intento è attiva e il plafond è capiente.",
          "Verificare che nella scheda IVA del documento sia presente la causale 'Non imponibile – esportatori abituali' con riferimento normativo art. 8 c.1 c).",
          "Controllare il riepilogo del plafond consumato nell'apposito report prima dell'invio.",
          "Generare il file XML e inviare allo SDI dalla console Fatturazione Elettronica.",
        ],
        notes: "TeamSystem aggiorna automaticamente il saldo plafond del cliente a ogni fattura emessa con questa causale. Verificare mensilmente il report 'Monitoraggio lettere d'intento' per evitare sforamenti.",
      },
    ],
  });

  // Aggiungo ERP mancanti per proc4 (Zona Franca)
  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc4.id,
        erpName: "Mexal (Passepartout)",
        stepByStepGuide: [
          "Ricevere e protocollare la lettera d'intento dal cliente tramite portale AdE.",
          "Archivi → Clienti → anagrafica cliente: inserire protocollo AdE e plafond disponibile nel campo 'Lettera d'intento'.",
          "Emissione Documenti → Nuovi → tipo fattura vendita: Mexal propone automaticamente N3.4 se la lettera d'intento è registrata e il plafond è capiente.",
          "Inserire le righe con codice IVA N3.4 e nel campo note riga il protocollo AdE.",
          "Passepartout SDI → verificare tipo TD01, Natura N3.4 nell'XML → inviare.",
          "Aggiornare il plafond consumato nell'apposito registro dopo ogni fattura emessa.",
        ],
        notes: "Mexal monitora automaticamente il plafond residuo per ogni cliente con lettera d'intento attiva. Stampare periodicamente il report 'Monitoraggio plafond' per evitare sforamenti.",
      },
      {
        procedureId: proc4.id,
        erpName: "Fatture in Cloud",
        stepByStepGuide: [
          "Ricevere il protocollo AdE della lettera d'intento dal cliente.",
          "Nell'anagrafica del cliente, nel campo 'Note interne', annotare il protocollo AdE e l'importo del plafond.",
          "Creare nuova fattura: selezionare il cliente e impostare manualmente l'aliquota 'N3.4 – Non imponibile esportatori abituali'.",
          "Aggiungere una riga descrittiva con il testo: 'Operazione non imponibile ex art. 8 c.1 lett. c DPR 633/72 – Lettera d'intento n. [PROTOCOLLO] del [DATA]'.",
          "Emettere e inviare allo SDI: tipo TD01, Natura N3.4.",
        ],
        notes: "Fatture in Cloud non gestisce automaticamente il monitoraggio del plafond: tenere un registro manuale (foglio Excel) delle fatture emesse in esenzione per non superare il plafond dichiarato dal cliente.",
      },
      {
        procedureId: proc4.id,
        erpName: "Sistemi / Profis",
        stepByStepGuide: [
          "Registrare la lettera d'intento in Archivi → Lettere d'intento associandola al cliente con protocollo AdE e plafond.",
          "Fatturazione Attiva → Nuova Fattura: Sistemi/Profis propone automaticamente N3.4 se la lettera d'intento è attiva.",
          "Verificare capienza del plafond nella finestra di riepilogo prima di confermare.",
          "Il sistema inserisce automaticamente il riferimento alla lettera d'intento nel campo note del documento.",
          "SDI → verificare tipo TD01, Natura N3.4 → inviare.",
        ],
        notes: "Sistemi/Profis aggiorna il saldo plafond del cliente ad ogni emissione. Il report 'Plafond Lettere d'Intento' è disponibile dal menu Report Contabilità.",
      },
      {
        procedureId: proc4.id,
        erpName: "Buffetti / Blustring",
        stepByStepGuide: [
          "Registrare la lettera d'intento del cliente in Acquisti/Vendite → Lettere d'Intento.",
          "Fatturazione → Nuova Fattura → selezionare il cliente: Blustring propone N3.4 se la lettera è attiva.",
          "Inserire le righe con aliquota N3.4 e il riferimento al protocollo AdE.",
          "Verificare che il tag <Natura>N3.4</Natura> sia presente nell'anteprima XML.",
          "Inviare allo SDI e aggiornare il plafond consumato nel registro della lettera d'intento.",
        ],
        notes: "Blustring include un alert automatico quando il plafond del cliente è quasi esaurito (configurable al 80% e al 95% del plafond totale). Attivarlo dall'anagrafica cliente.",
      },
    ],
  });

  // ─── Procedure 5: Nota di Credito (TD04) ───────────────────────────────────
  const proc5 = await prisma.accountingProcedure.create({
    data: {
      title: "Nota di Credito (TD04) – Storno o rettifica fattura",
      normativeSummary: "La nota di credito (TD04) si emette per rettificare in diminuzione una fattura già trasmessa allo SDI, nei casi di annullamento dell'operazione, recesso, mancato pagamento o variazione del corrispettivo (art. 26 DPR 633/72). L'imponibile e l'imposta devono essere riportati con segno positivo nel tracciato XML e devono rispecchiare la natura IVA della fattura originale. È obbligatorio indicare il riferimento alla fattura stornata nel campo <DatiFattureCollegate>.",
      electronicInvoicingFields: {
        tipo_documento: "TD04",
        natura_iva: "(stessa della fattura originale da stornare)",
        descrizione: "Nota di credito – variazione ex art. 26 DPR 633/72",
      },
      officialSources: [
        { source_name: "DPR 633/1972 – Art. 26 (Variazioni dell'imponibile o dell'imposta)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633~art26", target_paragraph: "Art. 26 – Casi e termini per l'emissione di note di variazione in diminuzione" },
        { source_name: "Agenzia delle Entrate – Guida FE, Sezione TD04", url: "https://www.agenziaentrate.gov.it/portale/documents/20143/288640/Guida_compilazione_FE_v1.8.pdf", target_paragraph: "Sezione 3.4 – Tipo Documento TD04: Nota di Credito" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc5.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Aprire la fattura originale da Fatture → Emesse e cliccare 'Crea Nota di Credito'.",
          "Danea pre-compila automaticamente tutti i campi speculari alla fattura originale.",
          "Verificare o modificare le righe (storno parziale: modificare quantità/importi; storno totale: lasciare invariato).",
          "Nella sezione 'Riferimento fattura collegata' verificare che numero e data della fattura originale siano riportati.",
          "Cliccare 'Salva' e poi 'Invia allo SDI': Danea assegna automaticamente il tipo TD04.",
          "Verificare nella sezione 'Fatturazione Elettronica' che lo stato diventi 'Consegnata'.",
        ],
        notes: "Se la fattura originale era già stata pagata, ricordarsi di gestire anche il rimborso o la compensazione con il cliente separatamente dalla registrazione contabile.",
      },
      {
        procedureId: proc5.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Accedere a Contabilità → Prima Nota → Registrazioni e richiamare la fattura originale.",
          "Dal menu azioni selezionare 'Genera Nota di Credito': il sistema crea un nuovo documento con causale NC.",
          "Verificare che il campo 'Fattura collegata' riporti correttamente numero e data della fattura originale.",
          "Modificare importi o righe se si tratta di storno parziale.",
          "Dal modulo Digital Hub Zucchetti → Documenti SDI, verificare il tipo TD04 e inviare allo SDI.",
          "Registrare la variazione IVA nel registro delle variazioni (automatica con causale NC).",
        ],
        notes: "Zucchetti gestisce automaticamente il doppio aggiornamento del registro IVA (storno vendite e nota credito). Verificare il corretto periodo di competenza IVA.",
      },
      {
        procedureId: proc5.id,
        erpName: "TeamSystem",
        stepByStepGuide: [
          "Aprire il documento originale da Fatturazione → Fatture Emesse.",
          "Selezionare 'Azioni' → 'Genera nota di credito': TeamSystem crea il documento TD04 con tutti i dati collegati.",
          "Verificare il blocco 'DatiFattureCollegate' che deve contenere numero, data e codice documento della fattura originaria.",
          "Per storni parziali, modificare le righe mantenendo le stesse aliquote IVA originali.",
          "Confermare e inviare allo SDI dalla console Fatturazione Elettronica.",
        ],
        notes: "TeamSystem permette di emettere nota di credito anche su fatture di anni precedenti: verificare il corretto trattamento fiscale (variazione in aumento del credito IVA nell'anno di emissione).",
      },
      {
        procedureId: proc5.id,
        erpName: "Mexal (Passepartout)",
        stepByStepGuide: [
          "Accedere al menu Emissione Documenti → Nuovi e selezionare tipo documento 'NC' (Nota di Credito).",
          "Nel campo 'Rif. documento' inserire numero e data della fattura originale da stornare.",
          "Richiamare le righe della fattura originale tramite 'Importa da documento' oppure inserirle manualmente con gli stessi codici IVA.",
          "Verificare che il sistema abbia compilato il campo <DatiFattureCollegate> nell'anteprima XML.",
          "Dal menu Gestione SDI → Invio documenti, selezionare il documento e procedere all'invio con tipo TD04.",
          "Registrare la variazione IVA tramite il modulo Prima Nota se non automatica.",
        ],
        notes: "In Mexal verificare che la causale contabile della nota di credito stia aggiornando correttamente il partitario cliente e il registro IVA vendite nel periodo corretto.",
      },
      {
        procedureId: proc5.id,
        erpName: "Fatture in Cloud",
        stepByStepGuide: [
          "Aprire la fattura originale da Fatture → Emesse.",
          "Cliccare il menu '···' (azioni) e selezionare 'Crea nota di credito': tutti i dati vengono pre-compilati.",
          "Verificare o modificare le righe per storni parziali.",
          "Fatture in Cloud riporta automaticamente il collegamento alla fattura originale.",
          "Cliccare 'Emetti' e poi 'Invia allo SDI': il tipo TD04 è impostato automaticamente.",
          "Monitorare lo stato dell'invio dalla sezione 'Stato SDI' del documento.",
        ],
        notes: "Fatture in Cloud mostra anche il saldo aggiornato del cliente dopo la nota di credito. Verificare che la nota sia riconciliata con la fattura originale nella sezione 'Pagamenti'.",
      },
    ],
  });

  // ─── Procedure 6: Split Payment – Scissione dei Pagamenti (PA) ──────────────
  const proc6 = await prisma.accountingProcedure.create({
    data: {
      title: "Split Payment – Scissione dei Pagamenti (fattura a PA)",
      normativeSummary: "Per le fatture emesse nei confronti di Pubbliche Amministrazioni e società soggette (elencate dal MEF), l'IVA è indicata in fattura ma non incassata dal fornitore: viene versata direttamente dall'ente acquirente all'Erario (art. 17-ter DPR 633/72). Nel tracciato XML SDI il tag <EsigibilitaIVA> deve essere impostato a 'S'. Il fornitore riceve solo l'imponibile; l'IVA non transita nei suoi conti bancari.",
      electronicInvoicingFields: {
        tipo_documento: "TD01",
        natura_iva: "(aliquota ordinaria, es. 22% – l'IVA è presente ma con EsigibilitaIVA = S)",
        descrizione: "Scissione dei pagamenti ex art. 17-ter DPR 633/72 – IVA non incassata dal cedente",
      },
      officialSources: [
        { source_name: "DPR 633/1972 – Art. 17-ter (Scissione dei pagamenti)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633~art17ter", target_paragraph: "Art. 17-ter – Operazioni effettuate nei confronti di pubbliche amministrazioni" },
        { source_name: "DM 23 gennaio 2015 (Elenco PA soggette a split payment)", url: "https://www.mef.gov.it/normativa/decreto-23-01-2015.html", target_paragraph: "Allegato A – Lista delle pubbliche amministrazioni soggette all'art. 17-ter" },
        { source_name: "Circolare AdE 1/E del 9 febbraio 2015", url: "https://www.agenziaentrate.gov.it/portale/documents/20143/262513/circ_2015_001e.pdf", target_paragraph: "Chiarimenti operativi sulla scissione dei pagamenti e i soggetti interessati" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc6.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Verificare che il cliente sia censito nell'anagrafica come 'Pubblica Amministrazione' (spuntare il flag 'Ente PA / Split Payment').",
          "Creare una nuova fattura di vendita: Danea abilita automaticamente la scissione dei pagamenti per quel cliente.",
          "Inserire le righe con l'aliquota IVA ordinaria (es. 22%): l'IVA compare in fattura ma il totale a pagare mostrerà solo l'imponibile.",
          "Verificare nell'anteprima XML che il tag <EsigibilitaIVA> riporti 'S' (Scissione dei pagamenti).",
          "Inviare allo SDI: il tipo documento rimane TD01.",
          "Registrare l'incasso solo per l'imponibile; l'IVA sarà versata direttamente dalla PA.",
        ],
        notes: "Ricordarsi di emettere la fattura elettronica verso PA tramite il Codice Univoco Ufficio (CUU/IPA) del destinatario, obbligatorio per le PA centrali e locali.",
      },
      {
        procedureId: proc6.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Nell'anagrafica del cliente PA attivare il flag 'Split Payment' e inserire il Codice Univoco Ufficio IPA.",
          "Accedere a Contabilità → Fatturazione Attiva → Nuova Fattura.",
          "Selezionare il cliente PA: Zucchetti imposta automaticamente EsigibilitàIVA = 'S' e il regime di scissione.",
          "Inserire le righe con aliquota IVA ordinaria; il programma separa visivamente imponibile e IVA.",
          "Generare il file XML dal Digital Hub: verificare la presenza del tag <EsigibilitaIVA>S</EsigibilitaIVA>.",
          "Inviare tramite SDI. La riconciliazione avverrà solo sull'importo imponibile incassato.",
        ],
        notes: "Zucchetti permette di configurare un automatismo: se il cliente ha il flag PA, la scissione viene applicata a ogni fattura senza intervento manuale.",
      },
      {
        procedureId: proc6.id,
        erpName: "TeamSystem",
        stepByStepGuide: [
          "Configurare l'anagrafica cliente con il flag 'PA – Split Payment' e il Codice Univoco Ufficio.",
          "Aprire Fatturazione Attiva → Nuova Fattura e selezionare il cliente PA.",
          "TeamSystem imposta automaticamente il regime di scissione: l'IVA è calcolata ma il netto da pagare esclude l'imposta.",
          "Verificare le condizioni di pagamento: il cliente pagherà solo l'imponibile.",
          "Dalla console SDI, verificare il tag EsigibilitàIVA='S' nell'XML prima dell'invio.",
          "Registrare l'incasso parziale (solo imponibile) alla ricezione del pagamento.",
        ],
        notes: "TeamSystem include un report 'Monitoraggio Split Payment' che elenca tutte le fatture PA con IVA sospesa, utile per la riconciliazione periodica.",
      },
      {
        procedureId: proc6.id,
        erpName: "Mexal (Passepartout)",
        stepByStepGuide: [
          "In Archivi → Clienti, aprire l'anagrafica del cliente PA e attivare 'Split Payment' e inserire il Codice Univoco IPA.",
          "Emissione Documenti → Nuova Fattura → tipo 'FAT PA': Mexal applica automaticamente la scissione.",
          "Inserire le righe con aliquota IVA ordinaria; il software visualizza separatamente 'Imponibile da incassare' e 'IVA a carico PA'.",
          "Verificare il tag <EsigibilitaIVA>S</EsigibilitaIVA> nell'anteprima XML.",
          "Inviare tramite Passepartout SDI specificando il canale PA (Codice Univoco Ufficio destinatario).",
          "In Prima Nota, registrare il credito solo per l'imponibile; creare un conto 'IVA c/PA' per il transitorio.",
        ],
        notes: "Mexal permette la stampa di un prospetto riepilogativo delle fatture PA con split payment, utile per la verifica mensile dell'IVA non incassata.",
      },
      {
        procedureId: proc6.id,
        erpName: "Fatture in Cloud",
        stepByStepGuide: [
          "Nell'anagrafica del cliente attivare 'Pubblica Amministrazione' e inserire il Codice Destinatario (IPA/CUU).",
          "Creare nuova fattura: Fatture in Cloud riconosce automaticamente i clienti PA soggetti a split payment.",
          "Inserire le righe con IVA ordinaria: il software mostra il dettaglio 'IVA versata da PA' nella preview.",
          "Verificare che nel riepilogo appaia la dicitura 'Scissione dei pagamenti – art. 17-ter'.",
          "Emettere e inviare allo SDI: il tag EsigibilitàIVA='S' è impostato automaticamente.",
          "Nella sezione Pagamenti, registrare solo l'incasso dell'imponibile quando arriva il bonifico dalla PA.",
        ],
        notes: "Fatture in Cloud mostra un alert automatico se si emette una fattura verso un cliente configurato come PA senza il flag split payment attivo, prevenendo errori.",
      },
    ],
  });

  // ─── Procedure 7: Ritenuta d'acconto su compenso professionale ──────────────
  const proc7 = await prisma.accountingProcedure.create({
    data: {
      title: "Compenso professionale con ritenuta d'acconto (RT01 – 20% IRPEF)",
      normativeSummary: "I professionisti (avvocati, consulenti, ingegneri, ecc.) soggetti a ritenuta d'acconto emettono fattura/parcella con imponibile, eventuale IVA ordinaria e una ritenuta del 20% a titolo di acconto IRPEF trattenuta dal committente sostituto d'imposta (art. 25 DPR 600/73). Il netto a pagare è imponibile + IVA – ritenuta. Nel tracciato XML SDI i dati vanno nel blocco <DatiRitenuta>: TipoRitenuta=RT01 (persone fisiche) o RT02 (persone giuridiche), ImportoRitenuta, AliquotaRitenuta=20.00, CausalePagamento=A.",
      electronicInvoicingFields: {
        tipo_documento: "TD01",
        natura_iva: "(aliquota ordinaria 22%, o N2.2 se forfettario)",
        descrizione: "Ritenuta d'acconto 20% IRPEF – RT01 – art. 25 DPR 600/73 – Causale A",
      },
      officialSources: [
        { source_name: "DPR 600/1973 – Art. 25 (Ritenute sui compensi)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1973-09-29;600~art25", target_paragraph: "Art. 25 – Ritenuta sui compensi per prestazioni di lavoro autonomo" },
        { source_name: "Agenzia delle Entrate – Guida FE, Sezione DatiRitenuta", url: "https://www.agenziaentrate.gov.it/portale/documents/20143/288640/Guida_compilazione_FE_v1.8.pdf", target_paragraph: "Sezione 2.1.1.5 – DatiRitenuta: TipoRitenuta, ImportoRitenuta, AliquotaRitenuta, CausalePagamento" },
        { source_name: "Tabella Causali pagamento ritenute (modello 770)", url: "https://www.agenziaentrate.gov.it/portale/web/guest/schede/dichiarazioni/770", target_paragraph: "Causale A – Prestazioni di lavoro autonomo rientranti nell'esercizio di arte o professione" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc7.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Creare una nuova fattura di vendita e selezionare il cliente committente.",
          "Inserire le righe del compenso con l'aliquota IVA ordinaria (22%) o N2.2 se in regime forfettario.",
          "In fondo alla fattura, nella sezione 'Ritenuta d'acconto', spuntare 'Applica ritenuta d'acconto'.",
          "Impostare: Aliquota 20%, Tipo RT01 (persona fisica) o RT02 (società), Causale pagamento: A.",
          "Verificare il riepilogo: Imponibile + IVA – Ritenuta = Netto a pagare.",
          "Generare e verificare il file XML: il blocco <DatiRitenuta> deve contenere tutti i campi.",
          "Inviare allo SDI. Richiedere al committente la Certificazione Unica (CU) a febbraio dell'anno successivo.",
        ],
        notes: "Se si è in regime forfettario, la ritenuta d'acconto NON si applica: indicarlo esplicitamente in fattura con la dicitura 'Operazione effettuata ai sensi dell'art. 1 c.67 L.190/2014 – non soggetta a ritenuta d'acconto'.",
      },
      {
        procedureId: proc7.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "In Fatturazione Attiva → Nuova Fattura, selezionare il tipo documento 'PARC' (Parcella/Compenso professionale).",
          "Inserire l'imponibile del compenso con il codice IVA ordinario.",
          "Nella sezione 'Ritenute', selezionare il codice ritenuta RT01 al 20% con causale A.",
          "Zucchetti calcola automaticamente: netto a pagare = imponibile + IVA – ritenuta.",
          "Verificare nell'XML il blocco <DatiRitenuta> prima dell'invio tramite Digital Hub.",
          "Il programma aggiorna automaticamente il registro delle ritenute subite per il modello 770.",
        ],
        notes: "Zucchetti Mago include un modulo 'Gestione Ritenute' che produce automaticamente il prospetto per la dichiarazione 770 di fine anno.",
      },
      {
        procedureId: proc7.id,
        erpName: "TeamSystem",
        stepByStepGuide: [
          "Aprire Fatturazione → Nuova Parcella Professionale.",
          "Inserire imponibile e IVA; nella sezione 'Ritenuta' selezionare RT01 (persone fisiche) al 20%, causale A.",
          "TeamSystem calcola il netto a pagare e popola automaticamente il blocco DatiRitenuta nell'XML.",
          "Verificare la correttezza dell'ImportoRitenuta e dell'AliquotaRitenuta nell'anteprima XML.",
          "Inviare allo SDI dalla console Fatturazione Elettronica.",
          "Il sistema registra la ritenuta subita nel registro apposito per il modello 770 annuale.",
        ],
        notes: "TeamSystem permette di stampare una 'ricevuta di compenso' (simile alla vecchia ricevuta professionale) da allegare alla parcella per documentazione interna.",
      },
      {
        procedureId: proc7.id,
        erpName: "Mexal (Passepartout)",
        stepByStepGuide: [
          "Emissione Documenti → Nuovi → tipo documento 'FCOL' (Fattura Collaboratori/Professionisti).",
          "Configurare l'anagrafica cliente come 'Sostituto d'imposta: SÌ'.",
          "Inserire le righe del compenso; nella sezione Ritenute selezionare TipoRitenuta RT01, aliquota 20%, causale A.",
          "Mexal calcola e mostra il dettaglio: imponibile, IVA, ritenuta trattenuta e netto a pagare.",
          "Verificare il blocco <DatiRitenuta> nell'anteprima XML prima dell'invio tramite Passepartout SDI.",
          "Il modulo 'Gestione Ritenute Subite' di Mexal aggiorna automaticamente il registro per la dichiarazione 770.",
        ],
        notes: "In Mexal è possibile stampare il Prospetto Compensi che riepiloga tutte le parcelle emesse nell'anno con le relative ritenute, utile per la compilazione del modello 770.",
      },
      {
        procedureId: proc7.id,
        erpName: "Fatture in Cloud",
        stepByStepGuide: [
          "Vai su Fatture → Nuova Fattura e seleziona il tipo 'Parcella / Compenso professionale'.",
          "Inserire le righe del compenso con IVA ordinaria.",
          "Nel pannello laterale destro, sotto 'Ritenuta d'acconto', spuntare l'opzione e impostare: Aliquota 20%, Tipo RT01, Causale A.",
          "Fatture in Cloud mostra in tempo reale il calcolo del netto a pagare.",
          "Emettere e inviare allo SDI: il blocco DatiRitenuta è compilato automaticamente.",
          "Nella sezione 'Ritenute subite' del gestionale è possibile monitorare il totale delle ritenute dell'anno.",
        ],
        notes: "Fatture in Cloud genera automaticamente un promemoria a fine anno per richiedere la Certificazione Unica ai committenti che hanno applicato ritenute durante l'anno.",
      },
    ],
  });

  // ─── Procedure 8: Cessione intracomunitaria beni (N3.2) ─────────────────────
  const proc8 = await prisma.accountingProcedure.create({
    data: {
      title: "Cessione intracomunitaria di beni a soggetto UE (N3.2)",
      normativeSummary: "Le cessioni di beni a soggetti passivi IVA stabiliti in altri Paesi UE (con numero IVA VIES attivo) sono non imponibili ai sensi dell'art. 41 DL 331/1993, con natura N3.2. La fattura deve riportare il numero IVA comunitario dell'acquirente verificato su VIES. Il cedente deve conservare prova dell'avvenuto trasferimento fisico dei beni nello Stato UE di destinazione (CMR firmato, documenti di trasporto) e presentare il modello INTRASTAT (mod. INTRA-1 bis) entro il 25 del mese successivo.",
      electronicInvoicingFields: {
        tipo_documento: "TD01",
        natura_iva: "N3.2",
        descrizione: "Non imponibile – cessione intracomunitaria ex art. 41 DL 331/1993",
      },
      officialSources: [
        { source_name: "DL 331/1993 – Art. 41 (Cessioni intracomunitarie non imponibili)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legge:1993-08-30;331~art41", target_paragraph: "Art. 41 – Cessioni intracomunitarie di beni non imponibili" },
        { source_name: "Regolamento UE 282/2011 – Prova della cessione intracomunitaria", url: "https://eur-lex.europa.eu/legal-content/IT/TXT/?uri=CELEX%3A32011R0282", target_paragraph: "Art. 45-bis – Presunzione di cessione intracomunitaria: documenti richiesti come prova" },
        { source_name: "Agenzia delle Entrate – Guida INTRASTAT", url: "https://www.agenziaentrate.gov.it/portale/web/guest/modelli-intrastat", target_paragraph: "Modello INTRA-1 bis – Cessioni intracomunitarie di beni, termini e modalità di presentazione" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc8.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Verificare la P.IVA comunitaria del cliente su VIES (ec.europa.eu/vies) prima di emettere la fattura.",
          "Nell'anagrafica cliente inserire il numero IVA nel formato internazionale (es. DE999999999) e spuntare 'Cliente UE'.",
          "Creare nuova fattura di vendita: Danea propone automaticamente 'Non imponibile UE' per i clienti configurati come UE.",
          "Selezionare esplicitamente il codice N3.2 (Cessione intracomunitaria beni) se non già proposto.",
          "Verificare nell'XML: tipo TD01, <Natura>N3.2</Natura>, partita IVA cliente nel formato corretto.",
          "Inviare allo SDI e conservare i documenti di trasporto (CMR) firmati dal destinatario come prova.",
          "Presentare il modello INTRASTAT INTRA-1 bis entro il 25 del mese successivo alla cessione.",
        ],
        notes: "Danea non genera automaticamente il file INTRASTAT: è necessario utilizzare il software Intra-web dell'Agenzia delle Dogane o un software dedicato per la compilazione e l'invio telematico.",
      },
      {
        procedureId: proc8.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Verificare la P.IVA del cliente su VIES e aggiornarla nell'anagrafica con il codice nazione UE.",
          "Accedere a Contabilità → Fatturazione Attiva → Nuova Fattura.",
          "Selezionare il codice IVA 'N3.2 – Cessione intracomunitaria beni' nelle righe del documento.",
          "Zucchetti verifica in automatico la coerenza tra codice IVA e codice nazione del cliente.",
          "Generare il file XML tramite Digital Hub: verificare tipo TD01 e Natura N3.2.",
          "Inviare allo SDI. Dal modulo Dichiarazioni → INTRASTAT generare il file INTRA-1 bis e inviarlo all'Agenzia delle Dogane.",
        ],
        notes: "Zucchetti Mago include il modulo INTRASTAT integrato che genera e invia telematicamente i modelli INTRA-1 bis mensili, aggregando automaticamente tutte le cessioni UE del periodo.",
      },
      {
        procedureId: proc8.id,
        erpName: "TeamSystem",
        stepByStepGuide: [
          "Validare la P.IVA comunitaria del cliente tramite il servizio VIES integrato in TeamSystem (Archivi → Clienti → Verifica VIES).",
          "Creare la fattura di vendita e selezionare il cliente UE.",
          "TeamSystem imposta automaticamente N3.2 per i clienti UE con flag 'Cessione intracomunitaria beni' attivo.",
          "Verificare che nel documento appaia la dicitura 'Operazione non imponibile ex art. 41 DL 331/93'.",
          "Inviare allo SDI dalla console Fatturazione Elettronica.",
          "Generare il file INTRASTAT dal modulo 'Dichiarazioni Periodiche → INTRASTAT' entro il 25 del mese successivo.",
        ],
        notes: "TeamSystem include un sistema di alert che avvisa quando si emette una fattura verso un cliente UE senza aver verificato la validità VIES nell'ultimo mese.",
      },
      {
        procedureId: proc8.id,
        erpName: "Mexal (Passepartout)",
        stepByStepGuide: [
          "Verificare la P.IVA comunitaria tramite la funzione integrata VIES in Mexal (Archivi → Clienti → Controllo VIES).",
          "Emissione Documenti → Nuovi → tipo 'FAUE-V' (Fattura Cessione UE Vendita).",
          "Mexal verifica in automatico la validità del numero VIES al salvataggio del documento.",
          "Selezionare il codice IVA N3.2 sulle righe: il sistema imposta automaticamente 'Non imponibile – art. 41'.",
          "Dall'anteprima XML verificare tipo TD01 e tag <Natura>N3.2</Natura> prima dell'invio tramite Passepartout SDI.",
          "Dalla funzione Dichiarazioni → Intrastat, generare e inviare telematicamente il modello INTRA-1 bis.",
        ],
        notes: "Mexal dispone di un modulo INTRASTAT completo che aggrega le cessioni del periodo, applica le soglie di esonero e invia telematicamente ad Agenzia Dogane. Passepartout aggiorna periodicamente le soglie INTRASTAT automaticamente.",
      },
      {
        procedureId: proc8.id,
        erpName: "Fatture in Cloud",
        stepByStepGuide: [
          "Nell'anagrafica cliente inserire il numero IVA comunitario nel campo 'Partita IVA' con prefisso paese (es. DE123456789).",
          "Creare nuova fattura: Fatture in Cloud riconosce il cliente UE e propone automaticamente il regime non imponibile.",
          "Selezionare 'N3.2 – Cessione intracomunitaria beni' se non già impostato.",
          "Aggiungere una riga descrittiva: 'Operazione non imponibile ex art. 41 DL 331/93 – P.IVA UE verificata su VIES'.",
          "Emettere e inviare allo SDI: tipo TD01, Natura N3.2.",
          "Per il modello INTRASTAT: Fatture in Cloud non genera il file INTRASTAT nativo – utilizzare il portale Agenzia delle Dogane (Intra-web) o un commercialista per la presentazione mensile.",
        ],
        notes: "Fatture in Cloud permette di esportare un report delle cessioni UE filtrato per periodo, utile per compilare manualmente o tramite commercialista il modello INTRASTAT mensile.",
      },
    ],
  });

  // ─── Procedure 9: TD18 – Acquisto beni intracomunitari ──────────────────────
  const proc9 = await prisma.accountingProcedure.create({
    data: {
      title: "Integrazione acquisto beni intracomunitari (TD18)",
      normativeSummary: "L'acquirente italiano soggetto passivo IVA che riceve beni da un fornitore UE deve integrare la fattura estera applicando l'IVA italiana tramite reverse charge. Il documento va trasmesso allo SDI con tipo TD18 entro il 15 del mese successivo a quello di ricezione della fattura originale. L'operazione si registra sia sul registro acquisti che sul registro vendite (doppia annotazione).",
      electronicInvoicingFields: {
        tipo_documento: "TD18",
        natura_iva: "N6.9",
        descrizione: "Integrazione acquisto beni intracomunitari – art. 46 DL 331/1993",
      },
      officialSources: [
        { source_name: "DL 331/1993 – Art. 46 (Integrazioni per acquisti intracomunitari)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legge:1993-08-30;331~art46", target_paragraph: "Art. 46 – Obbligo di integrazione delle fatture per acquisti di beni intracomunitari" },
        { source_name: "Agenzia delle Entrate – Guida FE, TD18", url: "https://www.agenziaentrate.gov.it/portale/documents/20143/288640/Guida_compilazione_FE_v1.8.pdf", target_paragraph: "Sezione 3.18 – Tipo Documento TD18" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc9.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Aprire Prima Nota e creare registrazione con causale 'FAUE-B' (Fattura Acquisto Beni UE).",
          "Inserire il fornitore UE con il suo numero IVA comunitario validato su VIES.",
          "Il sistema genera automaticamente la doppia registrazione IVA (acquisti + vendite).",
          "Dal Digital Hub selezionare il documento e impostare tipo TD18.",
          "Inviare allo SDI e verificare lo stato di consegna.",
        ],
        notes: "Verificare che la causale 'FAUE-B' sia distinta da 'FAEU' usata per i servizi (TD17). Il numero INTRASTAT INTRA-2 bis va presentato mensilmente.",
      },
      {
        procedureId: proc9.id,
        erpName: "TeamSystem",
        stepByStepGuide: [
          "Contabilità → Prima Nota → causale 'AUE-B' (Acquisto Beni CEE).",
          "Inserire la fattura con l'aliquota IVA italiana: il sistema effettua la doppia annotazione automatica.",
          "Dalla console SDI, verificare tipo TD18 e inviare entro il 15 del mese successivo.",
          "Generare modello INTRASTAT INTRA-2 bis dal modulo Dichiarazioni Periodiche.",
        ],
        notes: "Distinto dal TD17 (servizi): per i beni acquistati intra-UE si usa TD18. Il numero di partita IVA del cedente estero è obbligatorio nel file XML.",
      },
      {
        procedureId: proc9.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Acquisti → Nuovo → selezionare il fornitore UE con flag 'Cliente/Fornitore UE' attivo.",
          "Spuntare 'Acquisto beni intracomunitari' (non servizi): Danea assegna TD18.",
          "Inserire righe con aliquota IVA italiana; il software duplica la registrazione IVA.",
          "Strumenti → Invio fatture elettroniche → generare autofattura TD18 e inviare allo SDI.",
        ],
        notes: "Per Danea è necessario distinguere 'acquisto beni UE' da 'acquisto servizi UE' già in fase di inserimento per ottenere il tipo documento corretto (TD18 vs TD17).",
      },
      {
        procedureId: proc9.id,
        erpName: "Sistemi / Profis",
        stepByStepGuide: [
          "Accedere a Contabilità → Registrazioni → Nuova registrazione acquisto estero UE beni.",
          "Selezionare la causale specifica per acquisti intracomunitari di beni (tipo INT-B).",
          "Inserire i dati del fornitore UE con codice nazione e numero IVA VIES.",
          "Applicare l'aliquota IVA italiana: il sistema genera automaticamente la contropartita IVA vendite.",
          "Dal pannello FE/SDI impostare tipo documento TD18 e inviare telematicamente.",
        ],
        notes: "In Sistemi/Profis verificare che il codice causale INT-B abbia attivo il flag 'Doppio registro IVA intracomunitario beni'. Il modello INTRASTAT si genera dal menu Dichiarazioni.",
      },
      {
        procedureId: proc9.id,
        erpName: "Buffetti / Blustring",
        stepByStepGuide: [
          "Acquisti → Fatture Passive → Nuova → selezionare tipologia 'Acquisto Intra UE Beni'.",
          "Inserire il fornitore comunitario con relativo numero IVA UE.",
          "Blustring calcola automaticamente l'IVA italiana e crea il movimento speculare nel registro vendite.",
          "Dalla sezione 'Fatture Elettroniche' generare il file XML con tipo TD18.",
          "Inviare allo SDI e conservare la fattura del fornitore estero come documento probatorio.",
        ],
        notes: "Blustring include il modulo INTRASTAT: dal menu Dichiarazioni → INTRASTAT generare il modello INTRA-2 bis per gli acquisti intracomunitari di beni entro il 25 del mese.",
      },
    ],
  });

  // ─── Procedure 10: TD19 – Acquisto beni extra-UE art. 17 c.2 ────────────────
  const proc10 = await prisma.accountingProcedure.create({
    data: {
      title: "Autofattura acquisto beni da soggetti extra-UE (TD19)",
      normativeSummary: "Per gli acquisti di beni fisici da soggetti non stabiliti nell'UE che li cedono in Italia senza assolvimento dell'IVA in dogana (es. beni già in territorio italiano), il cessionario italiano deve emettere autofattura con TD19 e applicare il reverse charge. Diverso dalla normale importazione (che si sdogana con DDT doganale). L'autofattura va trasmessa allo SDI entro il giorno 15 del mese successivo.",
      electronicInvoicingFields: {
        tipo_documento: "TD19",
        natura_iva: "N6.9",
        descrizione: "Integrazione/autofattura acquisto beni da soggetto non UE ex art. 17 c.2 DPR 633/72",
      },
      officialSources: [
        { source_name: "DPR 633/1972 – Art. 17, comma 2 (Reverse charge extracomunitario beni)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633~art17", target_paragraph: "Art. 17, comma 2 – Soggetti passivi non stabiliti in Italia" },
        { source_name: "Agenzia delle Entrate – Guida FE, TD19", url: "https://www.agenziaentrate.gov.it/portale/documents/20143/288640/Guida_compilazione_FE_v1.8.pdf", target_paragraph: "Sezione 3.19 – Tipo Documento TD19" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc10.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Prima Nota → causale 'FAEXT-B' (Fattura Acquisto Beni Extracomunitario art. 17 c.2).",
          "Inserire il fornitore extra-UE con codice nazione e identificativo fiscale estero.",
          "Applicare l'aliquota IVA italiana: il sistema genera la doppia registrazione IVA.",
          "Dal Digital Hub impostare tipo TD19 e inviare allo SDI.",
        ],
        notes: "Attenzione: TD19 si usa quando i beni sono fisicamente in Italia e il fornitore non è stabilito in UE. Se si importa dall'estero con sdoganamento in dogana, si usa la bolla doganale (non TD19).",
      },
      {
        procedureId: proc10.id,
        erpName: "TeamSystem",
        stepByStepGuide: [
          "Prima Nota → causale 'AXT-B' (Acquisto Beni Extra-CEE art. 17).",
          "Inserire imponibile con aliquota IVA italiana; il sistema effettua la doppia annotazione IVA.",
          "Console SDI → tipo TD19 → inviare entro il 15 del mese successivo.",
        ],
        notes: "Non confondere con l'acquisto intracomunitario di beni (TD18): TD19 riguarda fornitore non stabilito in UE che cede beni già presenti in Italia.",
      },
      {
        procedureId: proc10.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Acquisti → Nuovo → selezionare fornitore extra-UE con flag 'Soggetto non UE' attivo.",
          "Spuntare 'Acquisto beni ex art. 17 c.2 (non importazione doganale)': Danea assegna TD19.",
          "Inserire righe con aliquota IVA italiana.",
          "Strumenti → Invio FE → generare e inviare autofattura TD19 allo SDI.",
        ],
        notes: "Diverso dall'importazione con sdoganamento (in quel caso si usa la bolla doganale come documento IVA). TD19 si applica solo quando non c'è passaggio doganale.",
      },
    ],
  });

  // ─── Procedure 11: TD24 – Fattura differita su DDT ──────────────────────────
  const proc11 = await prisma.accountingProcedure.create({
    data: {
      title: "Fattura differita su DDT (TD24)",
      normativeSummary: "È possibile emettere un'unica fattura riepilogativa entro il 15 del mese successivo per tutte le consegne effettuate nel mese verso lo stesso cliente, accompagnate da Documenti di Trasporto (DDT) o documenti equivalenti (art. 21 c.4 lett. a DPR 633/72). Nel tracciato XML SDI si usa il tipo TD24 e vanno obbligatoriamente indicati i riferimenti ai DDT nel blocco <DatiDDT>.",
      electronicInvoicingFields: {
        tipo_documento: "TD24",
        natura_iva: "(aliquota ordinaria della merce ceduta, es. 22%)",
        descrizione: "Fattura differita su DDT – art. 21 c.4 lett. a DPR 633/72",
      },
      officialSources: [
        { source_name: "DPR 633/1972 – Art. 21, comma 4, lett. a (Fattura differita)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633~art21", target_paragraph: "Art. 21, comma 4, lettera a – Emissione differita per cessioni di beni con DDT" },
        { source_name: "Agenzia delle Entrate – Guida FE, TD24", url: "https://www.agenziaentrate.gov.it/portale/documents/20143/288640/Guida_compilazione_FE_v1.8.pdf", target_paragraph: "Sezione 3.24 – Tipo Documento TD24" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc11.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Dal modulo Logistica/Magazzino, creare i DDT per ogni consegna del mese.",
          "Fatturazione Attiva → Fatturazione Differita → selezionare il cliente e il periodo.",
          "Zucchetti aggrega automaticamente tutti i DDT del periodo selezionato in un'unica fattura TD24.",
          "Verificare che il blocco <DatiDDT> contenga numero, data e fornitore di ogni DDT.",
          "Inviare allo SDI entro il 15 del mese successivo alle consegne.",
        ],
        notes: "La fattura differita è possibile solo per cessioni di beni accompagnati da DDT. Non si può applicare per le prestazioni di servizi che richiedono fattura immediata.",
      },
      {
        procedureId: proc11.id,
        erpName: "TeamSystem",
        stepByStepGuide: [
          "Creare i DDT da Magazzino → Documenti di Trasporto per ogni spedizione.",
          "Fatturazione → Fatturazione Differita → selezionare cliente e mese da fatturare.",
          "TeamSystem crea automaticamente la fattura riepilogativa collegando tutti i DDT (blocco DatiDDT).",
          "Impostare tipo TD24 dalla console SDI e inviare entro il 15 del mese successivo.",
        ],
        notes: "TeamSystem permette di configurare automatismi mensili per la fatturazione differita: il sistema genera in automatico le fatture TD24 alla mezzanotte del 14 del mese successivo.",
      },
      {
        procedureId: proc11.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Creare i DDT dalla sezione Magazzino → DDT per ogni consegna.",
          "Fatture → Crea fattura da DDT → selezionare il cliente e spuntare tutti i DDT del mese.",
          "Danea crea la fattura riepilogativa con i riferimenti DDT nel campo note.",
          "Nella sezione FE impostare tipo TD24 e inviare allo SDI.",
          "Verificare il blocco <DatiDDT> nell'anteprima XML prima dell'invio.",
        ],
        notes: "In Danea è possibile selezionare DDT multipli e creare la fattura differita anche solo per alcuni: utile per clienti con ordini parziali.",
      },
      {
        procedureId: proc11.id,
        erpName: "Mexal (Passepartout)",
        stepByStepGuide: [
          "Gestione Magazzino → emettere i DDT per ogni consegna del mese.",
          "Emissione Documenti → Fatturazione Differita → selezionare il periodo e il cliente.",
          "Mexal consolida i DDT in un'unica fattura con tipo TD24 e popola automaticamente il blocco DatiDDT.",
          "Passepartout SDI → inviare il documento entro il 15 del mese.",
        ],
        notes: "Mexal supporta la fatturazione differita multicliente: è possibile generare tutte le fatture TD24 del mese in blocco per tutti i clienti con DDT aperti.",
      },
      {
        procedureId: proc11.id,
        erpName: "Fatture in Cloud",
        stepByStepGuide: [
          "Creare i DDT dalla sezione Magazzino per ogni consegna.",
          "Fatture → Nuova Fattura → 'Crea da DDT': selezionare i DDT del mese per quel cliente.",
          "Impostare tipo TD24 dal campo 'Tipo documento' prima di salvare.",
          "Inviare allo SDI verificando che appaiano i riferimenti ai DDT nel documento.",
        ],
        notes: "Fatture in Cloud mostra un alert se si tenta di inviare una fattura TD24 oltre il 15 del mese successivo, ricordando il termine di legge.",
      },
    ],
  });

  // ─── Procedure 12: TD27 – Autoconsumo e cessioni gratuite ───────────────────
  const proc12 = await prisma.accountingProcedure.create({
    data: {
      title: "Autoconsumo e cessioni gratuite di beni (TD27)",
      normativeSummary: "Il prelievo di beni dall'impresa per uso personale dell'imprenditore (autoconsumo) o la cessione gratuita di beni a clienti/dipendenti (omaggi) costituisce operazione imponibile ai fini IVA se i beni avevano dato diritto a detrazione all'acquisto (art. 2 c.2 n.5 DPR 633/72). Si emette autofattura con tipo TD27 per documentare l'operazione allo SDI. Per omaggi di valore unitario ≤ 50€ si applica la detraibilità piena; per valori superiori l'IVA è indetraibile.",
      electronicInvoicingFields: {
        tipo_documento: "TD27",
        natura_iva: "(aliquota ordinaria del bene ceduto gratuitamente)",
        descrizione: "Autoconsumo / cessione gratuita beni – art. 2 c.2 n.5 DPR 633/72",
      },
      officialSources: [
        { source_name: "DPR 633/1972 – Art. 2, comma 2, n. 5 (Cessioni a titolo gratuito)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633~art2", target_paragraph: "Art. 2, comma 2, n.5 – Operazioni assimilate alle cessioni di beni" },
        { source_name: "Agenzia delle Entrate – Guida FE, TD27", url: "https://www.agenziaentrate.gov.it/portale/documents/20143/288640/Guida_compilazione_FE_v1.8.pdf", target_paragraph: "Sezione 3.27 – Tipo Documento TD27" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc12.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Contabilità → Fatturazione Attiva → Nuova Fattura → tipo 'Autofattura TD27'.",
          "Il destinatario è la propria azienda (stessa P.IVA del cedente) per autoconsumo, oppure il donatario per omaggi.",
          "Inserire il bene ceduto con il valore normale (prezzo di costo o di mercato) e la relativa aliquota IVA.",
          "Dal Digital Hub verificare tipo TD27 e inviare allo SDI.",
          "Registrare contabilmente l'IVA come costo non deducibile se l'omaggio supera 50€ per unità.",
        ],
        notes: "Per omaggi a clienti ≤ 50€/unità: IVA detraibile al 100% e non si addebita l'IVA al cliente. Per omaggi > 50€: IVA indetraibile per l'azienda. Per omaggi ai dipendenti vedere il trattamento IRPEF fringe benefit.",
      },
      {
        procedureId: proc12.id,
        erpName: "TeamSystem",
        stepByStepGuide: [
          "Fatturazione → Nuova Autofattura → selezionare tipo TD27.",
          "Inserire il bene ceduto gratuitamente con il valore normale e l'aliquota IVA corrispondente.",
          "Per autoconsumo: il cessionario è l'imprenditore stesso (inserire la propria P.IVA).",
          "Console SDI → verificare TD27 → inviare allo SDI.",
          "Registrare in Prima Nota la variazione di magazzino e l'eventuale IVA indetraibile.",
        ],
        notes: "TeamSystem distingue automaticamente autoconsumo (cessionario = cedente) da cessione gratuita (cessionario diverso): impostare correttamente il destinatario prima dell'invio.",
      },
      {
        procedureId: proc12.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Fatture → Nuova Fattura → nel campo cliente inserire la propria ragione sociale (per autoconsumo).",
          "Selezionare i beni prelevati/ceduti gratuitamente con valore normale e aliquota IVA.",
          "In FE impostare tipo documento TD27.",
          "Inviare allo SDI e registrare il prelievo di magazzino.",
        ],
        notes: "Danea richiede che il 'cliente' dell'autofattura TD27 sia un'anagrafica valida: creare un'anagrafica con la propria ragione sociale e P.IVA se non ancora presente.",
      },
    ],
  });

  // ─── Procedure 13: TD20 – Autofattura per regolarizzazione ──────────────────
  const proc13 = await prisma.accountingProcedure.create({
    data: {
      title: "Autofattura per regolarizzazione (TD20 – fattura mancante o irregolare)",
      normativeSummary: "Se il fornitore non emette la fattura entro 4 mesi dall'operazione, oppure emette una fattura irregolare, il cessionario/committente deve regolarizzarsi emettendo un'autofattura TD20 entro il 30° giorno successivo alla scadenza dei 4 mesi (art. 6 c.8 D.Lgs. 471/97). L'autofattura deve essere trasmessa allo SDI e versata separatamente l'IVA mancante, con eventuale ravvedimento operoso per le sanzioni.",
      electronicInvoicingFields: {
        tipo_documento: "TD20",
        natura_iva: "(aliquota dovuta sull'operazione non documentata)",
        descrizione: "Autofattura per regolarizzazione – art. 6 c.8 D.Lgs. 471/97",
      },
      officialSources: [
        { source_name: "D.Lgs. 471/1997 – Art. 6, comma 8 (Autofattura per mancata ricezione)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:1997-12-18;471~art6", target_paragraph: "Art. 6, comma 8 – Sanzioni per l'acquirente in caso di omessa o irregolare fatturazione" },
        { source_name: "Agenzia delle Entrate – Guida FE, TD20", url: "https://www.agenziaentrate.gov.it/portale/documents/20143/288640/Guida_compilazione_FE_v1.8.pdf", target_paragraph: "Sezione 3.20 – Tipo Documento TD20" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc13.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Verificare il decorso dei 4 mesi dall'operazione senza ricezione fattura dal fornitore.",
          "Contabilità → Prima Nota → causale 'AF-REG' (Autofattura Regolarizzazione TD20).",
          "Inserire il valore dell'operazione con l'aliquota IVA dovuta.",
          "Digital Hub → tipo TD20 → inviare allo SDI.",
          "Versare separatamente l'IVA tramite F24 con codice tributo 6099 entro il giorno dell'autofattura.",
          "Valutare il ravvedimento operoso per le sanzioni se già scaduti i termini.",
        ],
        notes: "Il versamento IVA tramite F24 è separato dalla normale liquidazione periodica. Conservare documentazione dell'inadempienza del fornitore (es. diffida scritta).",
      },
      {
        procedureId: proc13.id,
        erpName: "Fatture in Cloud",
        stepByStepGuide: [
          "Fatture → Nuova Fattura → selezionare il fornitore inadempiente come 'cliente'.",
          "Inserire i dati dell'operazione non documentata con la corretta aliquota IVA.",
          "Impostare tipo documento TD20 nel campo apposito.",
          "Inviare allo SDI e annotare nel registro acquisti la data di invio.",
          "Procedere con il versamento dell'IVA tramite F24 con codice 6099.",
        ],
        notes: "Fatture in Cloud non gestisce automaticamente il versamento F24: è necessario procedere manualmente con il pagamento dell'IVA dopo l'invio allo SDI.",
      },
    ],
  });

  // ─── Procedure 14: Nota di debito (TD05) ────────────────────────────────────
  const proc14 = await prisma.accountingProcedure.create({
    data: {
      title: "Nota di debito (TD05) – Aumento del corrispettivo fatturato",
      normativeSummary: "La nota di debito (TD05) si emette per rettificare in aumento una fattura già emessa allo SDI (es. adeguamento prezzo, addebito interessi di mora, correzione di un importo fatturato in meno). L'emissione è regolata dall'art. 26 c.1 DPR 633/72. Nel tracciato XML va indicato il riferimento alla fattura originale nel campo <DatiFattureCollegate>.",
      electronicInvoicingFields: {
        tipo_documento: "TD05",
        natura_iva: "(stessa aliquota della fattura originale rettificata)",
        descrizione: "Nota di debito – variazione in aumento ex art. 26 c.1 DPR 633/72",
      },
      officialSources: [
        { source_name: "DPR 633/1972 – Art. 26, comma 1 (Note di variazione in aumento)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633~art26", target_paragraph: "Art. 26, comma 1 – Variazioni in aumento dell'imponibile o dell'imposta" },
        { source_name: "Agenzia delle Entrate – Guida FE, TD05", url: "https://www.agenziaentrate.gov.it/portale/documents/20143/288640/Guida_compilazione_FE_v1.8.pdf", target_paragraph: "Sezione 3.5 – Tipo Documento TD05: Nota di Debito" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc14.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Fatture → Emesse → aprire la fattura originale.",
          "Azioni → 'Crea Nota di Debito': Danea pre-compila il documento con tipo TD05.",
          "Inserire solo la differenza in aumento (importo aggiuntivo) e la relativa IVA.",
          "Verificare il collegamento alla fattura originale nel campo <DatiFattureCollegate>.",
          "Inviare allo SDI dalla sezione Fatturazione Elettronica.",
        ],
        notes: "La nota di debito non richiede il consenso del cliente (a differenza della nota di credito). Il cliente riceve comunque la notifica dallo SDI.",
      },
      {
        procedureId: proc14.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Prima Nota → Fatturazione → richiamare la fattura originale.",
          "Azioni → 'Genera Nota di Debito': il sistema crea documento con causale ND e tipo TD05.",
          "Inserire l'importo aggiuntivo da addebitare con la stessa aliquota IVA della fattura originale.",
          "Digital Hub → verificare TD05 e inviare allo SDI.",
        ],
        notes: "Zucchetti aggiorna automaticamente il partitario cliente con il nuovo importo. Verificare che il periodo IVA della nota di debito sia corretto.",
      },
      {
        procedureId: proc14.id,
        erpName: "Fatture in Cloud",
        stepByStepGuide: [
          "Fatture → Emesse → trovare la fattura originale.",
          "Cliccare '···' → 'Crea nota di debito': tipo TD05 viene impostato automaticamente.",
          "Inserire il solo importo in aumento da addebitare.",
          "Emettere e inviare allo SDI: la nota di debito viene collegata automaticamente alla fattura originale.",
        ],
        notes: "Fatture in Cloud aggiunge automaticamente la nota di debito alla sezione 'Documenti correlati' della fattura originale per facilitare il monitoraggio.",
      },
    ],
  });

  // ─── Procedure 15: Reverse charge elettronica e telefonia (art. 17 c.6 b) ───
  const proc15 = await prisma.accountingProcedure.create({
    data: {
      title: "Reverse charge settore elettronico e telefonia (art. 17 c.6 lett. b)",
      normativeSummary: "Le cessioni di cellulari, tablet, computer, componenti hardware, console di gioco e simili dispositivi elettronici tra soggetti passivi IVA nazionali sono soggette a inversione contabile (reverse charge) ai sensi dell'art. 17 c.6 lett. b DPR 633/72. Il cedente emette fattura senza IVA con natura N6.2. Il cessionario deve integrare con TD16 e registrare sia in acquisti che in vendite.",
      electronicInvoicingFields: {
        tipo_documento: "TD16",
        natura_iva: "N6.2",
        descrizione: "Reverse charge – cessione dispositivi elettronici art. 17 c.6 lett. b DPR 633/72",
      },
      officialSources: [
        { source_name: "DPR 633/1972 – Art. 17, c.6 lett. b (Elettronica)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633~art17", target_paragraph: "Art. 17, comma 6, lettera b – Reverse charge per dispositivi elettronici e telefonia" },
        { source_name: "Circolare AdE 59/E del 2010 (Reverse charge elettronica)", url: "https://www.agenziaentrate.gov.it/portale/documents/20143/262513/circ_2010_059e.pdf", target_paragraph: "Paragrafo 3 – Ambito applicativo: cellulari, componenti hardware, tablet, console" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc15.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Prima Nota → causale 'REV_EL' (Reverse Charge Elettronica art. 17 c.6 b).",
          "Registrare la fattura fornitore con codice IVA N6.2 sul registro acquisti.",
          "Il sistema crea automaticamente la contropartita sul registro vendite.",
          "Digital Hub → tipo TD16 → inviare autofattura integrativa allo SDI.",
        ],
        notes: "Applicabile solo a transazioni B2B (tra soggetti passivi IVA). Se il cessionario è un privato o un'azienda non soggetta IVA, si applica l'IVA ordinaria.",
      },
      {
        procedureId: proc15.id,
        erpName: "TeamSystem",
        stepByStepGuide: [
          "Prima Nota → causale 'RCE-EL' (RC Elettronica/Telefonia).",
          "Inserire la fattura con aliquota di esenzione N6.2: il sistema effettua la doppia registrazione.",
          "Console SDI → tipo TD16 → inviare entro i termini.",
        ],
        notes: "TeamSystem include un report specifico per il reverse charge elettronico che elenca tutte le transazioni soggette alla normativa, utile per i controlli periodici.",
      },
      {
        procedureId: proc15.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Acquisti → Nuova fattura passiva → selezionare il fornitore.",
          "Spuntare 'Reverse charge – Art. 17 c.6 lett. b (Elettronica)'.",
          "Selezionare aliquota N6.2: Danea crea la doppia registrazione IVA.",
          "Strumenti → FE → generare TD16 e inviare allo SDI.",
        ],
        notes: "Verificare in Danea che il codice aliquota N6.2 sia configurato separatamente da N6.3 (edilizia) per evitare confusioni nella liquidazione IVA.",
      },
    ],
  });

  // ─── Procedure 16: Reverse charge pulizie (art. 17 c.6 a-ter) ───────────────
  const proc16 = await prisma.accountingProcedure.create({
    data: {
      title: "Reverse charge servizi di pulizia, demolizione e installazione (art. 17 c.6 lett. a-ter)",
      normativeSummary: "I servizi di pulizia, demolizione, installazione di impianti e completamento di edifici ceduti tra soggetti passivi IVA sono soggetti a reverse charge con natura N6.7 (art. 17 c.6 lett. a-ter DPR 633/72, introdotto dalla L. 190/2014). Il prestatore emette fattura senza IVA con N6.7; il committente integra con TD16. Applicabile solo quando ENTRAMBE le parti sono soggetti passivi IVA.",
      electronicInvoicingFields: {
        tipo_documento: "TD16",
        natura_iva: "N6.7",
        descrizione: "Reverse charge – pulizie, demolizione, installazione impianti, completamento edifici art. 17 c.6 lett. a-ter",
      },
      officialSources: [
        { source_name: "DPR 633/1972 – Art. 17, c.6 lett. a-ter (pulizie/demolizioni)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633~art17", target_paragraph: "Art. 17, comma 6, lettera a-ter – Servizi di pulizia, demolizione, installazione impianti e completamento edifici" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc16.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Prima Nota → causale 'REV_PUL' (Reverse Charge Pulizie/Demolizioni art. 17 c.6 a-ter).",
          "Registrare la fattura con codice IVA N6.7 sul registro acquisti.",
          "Il sistema genera la contropartita automatica sul registro vendite.",
          "Digital Hub → tipo TD16 → inviare autofattura integrativa allo SDI.",
        ],
        notes: "N6.7 riguarda i servizi di pulizia e demolizione; N6.3 riguarda il subappalto edile. Sono due codici distinti – non confondere.",
      },
      {
        procedureId: proc16.id,
        erpName: "TeamSystem",
        stepByStepGuide: [
          "Prima Nota → causale 'RCP-DEM' (RC Pulizie/Demolizioni).",
          "Aliquota N6.7 sul documento: TeamSystem effettua la doppia registrazione IVA.",
          "Console SDI → tipo TD16 → inviare allo SDI.",
        ],
        notes: "Verificare che i lavori rientrino effettivamente nelle categorie previste: pulizia di edifici, demolizioni, installazione impianti (idraulici, elettrici, termici), completamento edifici.",
      },
      {
        procedureId: proc16.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Acquisti → Nuova fattura → selezionare fornitore impresa di pulizie/demolizioni.",
          "Spuntare 'Reverse charge – Art. 17 c.6 lett. a-ter (Pulizie/Demolizioni)'.",
          "Aliquota N6.7: Danea gestisce la doppia annotazione IVA.",
          "Strumenti → FE → generare e inviare TD16 allo SDI.",
        ],
        notes: "Il reverse charge pulizie si applica solo B2B. Se il committente è un privato o un ente non commerciale, si applica l'IVA ordinaria senza inversione.",
      },
    ],
  });

  // ─── Procedure 17: Split Payment enti non PA (società quotate/controllate) ──
  const proc17 = await prisma.accountingProcedure.create({
    data: {
      title: "Split Payment esteso – Società quotate e controllate dallo Stato",
      normativeSummary: "Il regime di scissione dei pagamenti (art. 17-ter DPR 633/72) è stato esteso alle società quotate in borsa e alle società controllate dallo Stato/enti pubblici (DM 9 gennaio 2018). Le fatture emesse verso questi soggetti devono riportare il tag <EsigibilitaIVA>S</EsigibilitaIVA> nel tracciato XML. L'elenco aggiornato è disponibile sul sito MEF. A differenza delle PA, questi soggetti non usano il Codice Univoco IPA ma un normale indirizzo email PEC.",
      electronicInvoicingFields: {
        tipo_documento: "TD01",
        natura_iva: "(aliquota ordinaria 22% – EsigibilitaIVA = S)",
        descrizione: "Split Payment esteso – società quotate e controllate MEF – DM 9 gennaio 2018",
      },
      officialSources: [
        { source_name: "DM 9 gennaio 2018 (Split Payment esteso)", url: "https://www.mef.gov.it/normativa/decreto-09-01-2018.html", target_paragraph: "Allegato A – Elenco delle società quotate e controllate soggette a split payment" },
        { source_name: "DPR 633/1972 – Art. 17-ter", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633~art17ter", target_paragraph: "Art. 17-ter, comma 1-bis – Estensione a società controllate e quotate" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc17.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Verificare sul sito MEF se il cliente rientra nell'elenco soggetti a split payment esteso.",
          "Anagrafica cliente → attivare il flag 'Split Payment' (anche se non è PA classica).",
          "Creare la fattura: Danea applica EsigibilitàIVA=S anche per soggetti non PA se il flag è attivo.",
          "L'indirizzo di consegna SDI è la PEC del cliente (non il codice IPA).",
          "Inviare allo SDI: verificare il tag <EsigibilitaIVA>S</EsigibilitaIVA> nell'XML.",
        ],
        notes: "Il MEF aggiorna periodicamente gli elenchi. Verificare all'inizio di ogni anno se i clienti abituali rientrano ancora nell'elenco o vi sono stati aggiunti nuovi soggetti.",
      },
      {
        procedureId: proc17.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Aggiornare l'anagrafica cliente con il flag 'Split Payment Esteso' (distinto dal flag PA).",
          "Emettere la fattura ordinaria TD01: Zucchetti applica automaticamente EsigibilitàIVA=S.",
          "L'indirizzo SDI è la PEC del cliente (non IPA/CUU).",
          "Digital Hub → verificare il tag EsigibilitàIVA='S' nell'XML → inviare.",
        ],
        notes: "Zucchetti permette di importare periodicamente gli elenchi MEF aggiornati per verificare automaticamente se i clienti sono soggetti a split payment esteso.",
      },
    ],
  });

  // ─── Procedure 18: Fattura a PA con CIG/CUP ──────────────────────────────────
  const proc18 = await prisma.accountingProcedure.create({
    data: {
      title: "Fattura a Pubblica Amministrazione con CIG e/o CUP (tracciabilità appalti)",
      normativeSummary: "Le fatture relative a contratti di appalto, fornitura o servizi verso la PA soggetti alla tracciabilità dei flussi finanziari (L. 136/2010) devono obbligatoriamente riportare il CIG (Codice Identificativo Gara) e/o il CUP (Codice Unico Progetto). Nel tracciato XML SDI questi codici vanno inseriti nel blocco <DatiOrdineAcquisto> o <DatiContratto>. In assenza del CIG la fattura non viene accettata dal sistema di pagamento PA.",
      electronicInvoicingFields: {
        tipo_documento: "TD01",
        natura_iva: "(aliquota ordinaria o split payment se PA soggetta) + EsigibilitaIVA=S",
        descrizione: "Fattura PA con CIG/CUP – tracciabilità flussi finanziari ex L. 136/2010",
      },
      officialSources: [
        { source_name: "Legge 136/2010 – Tracciabilità flussi finanziari (CIG)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:legge:2010-08-13;136", target_paragraph: "Art. 3 – Obblighi di tracciabilità dei flussi finanziari per appalti pubblici" },
        { source_name: "Agenzia delle Entrate – Guida FE: DatiOrdineAcquisto e DatiContratto", url: "https://www.agenziaentrate.gov.it/portale/documents/20143/288640/Guida_compilazione_FE_v1.8.pdf", target_paragraph: "Sezione 2.1.2 – DatiOrdineAcquisto, DatiContratto, DatiConvenzione, DatiRicezione" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc18.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Nell'anagrafica del contratto/ordine PA inserire il CIG e/o il CUP nei campi dedicati.",
          "Fatturazione Attiva → Nuova Fattura PA → selezionare il contratto/ordine con CIG.",
          "Zucchetti popola automaticamente il blocco <DatiOrdineAcquisto> con il CIG se collegato all'ordine.",
          "Verificare nell'XML che il campo <CodiceCIG> riporti il valore corretto.",
          "Attivare il flag Split Payment se il cliente è PA (EsigibilitàIVA=S).",
          "Digital Hub → verificare e inviare allo SDI tramite canale PA (Codice Univoco IPA).",
        ],
        notes: "Il CIG va richiesto alla stazione appaltante prima dell'emissione della fattura. Senza CIG i pagamenti PA vengono bloccati dall'Agenzia delle Entrate.",
      },
      {
        procedureId: proc18.id,
        erpName: "TeamSystem",
        stepByStepGuide: [
          "Archivi → Contratti PA → inserire i dati del contratto con CIG e CUP.",
          "Fatturazione PA → Nuova Fattura → collegare al contratto: TeamSystem popola automaticamente i tag DatiContratto/DatiOrdine.",
          "Verificare CIG e CUP nell'anteprima XML.",
          "Console SDI → inviare tramite indirizzo IPA della PA destinataria.",
        ],
        notes: "TeamSystem include un modulo PA che verifica la presenza del CIG prima dell'invio allo SDI, impedendo l'invio di fatture prive del codice obbligatorio.",
      },
      {
        procedureId: proc18.id,
        erpName: "Fatture in Cloud",
        stepByStepGuide: [
          "Fatture → Nuova Fattura → selezionare il cliente PA.",
          "Nel blocco 'Dati ordine/contratto' inserire il numero CIG nel campo 'Codice CIG' e il CUP se applicabile.",
          "Impostare il Codice Destinatario IPA della PA nella scheda cliente.",
          "Attivare il flag Split Payment (EsigibilitàIVA=S) se la PA è soggetta.",
          "Emettere e inviare allo SDI: verificare la presenza del CIG nell'XML prima dell'invio.",
        ],
        notes: "Fatture in Cloud richiede la compilazione manuale del CIG: non recupera automaticamente i dati dall'ordine. Verificare che il CIG inserito corrisponda a quello dell'ordine MEPA/gara.",
      },
    ],
  });

  // ─── Procedure 19: Fattura esente IVA art. 10 (N1) ──────────────────────────
  const proc19 = await prisma.accountingProcedure.create({
    data: {
      title: "Fattura per operazioni esenti IVA (N1 – art. 10 DPR 633/72)",
      normativeSummary: "Le operazioni esenti IVA (art. 10 DPR 633/72) riguardano servizi finanziari, assicurativi, sanitari, educativi e locazioni di fabbricati non strumentali. Si emette fattura con natura N1 senza addebito IVA. L'esenzione limita o esclude il diritto alla detrazione dell'IVA sugli acquisti (pro-rata). Per i soggetti che effettuano operazioni miste (esenti + imponibili) è necessario il calcolo del pro-rata di detraibilità.",
      electronicInvoicingFields: {
        tipo_documento: "TD01",
        natura_iva: "N1",
        descrizione: "Esente da IVA – art. 10 DPR 633/72 (specificare il numero del comma applicabile)",
      },
      officialSources: [
        { source_name: "DPR 633/1972 – Art. 10 (Operazioni esenti)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633~art10", target_paragraph: "Art. 10 – Elenco tassativo delle operazioni esenti dall'imposta sul valore aggiunto" },
        { source_name: "DPR 633/1972 – Art. 19 (Pro-rata di detraibilità)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633~art19", target_paragraph: "Art. 19 – Detrazione dell'imposta e calcolo del pro-rata per operatori misti" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc19.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Fatture → Nuova Fattura → selezionare il cliente.",
          "Per ogni riga di servizio, nel campo Aliquota IVA selezionare 'Esente – N1 (art. 10)'.",
          "Inserire la descrizione dettagliata del servizio esente e il riferimento normativo specifico (es. 'Servizi finanziari ex art. 10 n.1').",
          "Verificare nell'XML il tag <Natura>N1</Natura>.",
          "Inviare allo SDI: tipo TD01, Natura N1, nessuna IVA addebitata.",
        ],
        notes: "L'esenzione limita la detrazione IVA sugli acquisti del professionista/impresa. Calcolare annualmente il pro-rata di detraibilità se si effettuano sia operazioni imponibili che esenti.",
      },
      {
        procedureId: proc19.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Nel piano delle aliquote IVA, configurare il codice 'ES-N1' per le operazioni esenti art. 10.",
          "Fatturazione Attiva → Nuova Fattura → usare il codice ES-N1 sulle righe.",
          "Zucchetti esclude automaticamente queste operazioni dal calcolo della liquidazione IVA periodica.",
          "Digital Hub → tipo TD01, Natura N1 → inviare allo SDI.",
          "Aggiornare il calcolo del pro-rata a fine anno se sono presenti anche operazioni imponibili.",
        ],
        notes: "Zucchetti include il modulo Pro-Rata IVA che calcola automaticamente la percentuale di detraibilità in base al rapporto operazioni imponibili/totale operazioni dell'anno precedente.",
      },
    ],
  });

  // ─── Procedure 20: Regime OSS/MOSS – e-commerce UE B2C ──────────────────────
  const proc20 = await prisma.accountingProcedure.create({
    data: {
      title: "Regime OSS/MOSS – vendite e-commerce UE a consumatori privati (B2C)",
      normativeSummary: "I venditori online italiani che effettuano vendite di beni/servizi digitali a consumatori finali in altri Paesi UE (B2C), superando la soglia di 10.000€ annui, devono applicare l'IVA del paese del consumatore e versarla tramite il regime OSS (One Stop Shop) all'Agenzia delle Entrate, che la riversa agli altri Stati UE. Le fatture non vengono trasmesse allo SDI (non è obbligo per B2C UE), ma devono essere registrate nel registro OSS.",
      electronicInvoicingFields: {
        tipo_documento: "TD01",
        natura_iva: "(aliquota IVA del paese UE del consumatore – non aliquota italiana)",
        descrizione: "Vendita B2C UE – Regime OSS – IVA paese destinazione – art. 74-quinquies DPR 633/72",
      },
      officialSources: [
        { source_name: "DPR 633/1972 – Art. 74-quinquies (Regime OSS)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633~art74quinquies", target_paragraph: "Art. 74-quinquies – Regime speciale per i servizi di telecomunicazione, TBE e OSS" },
        { source_name: "Agenzia delle Entrate – Regime OSS: guida operativa", url: "https://www.agenziaentrate.gov.it/portale/web/guest/oss", target_paragraph: "Registrazione, dichiarazione trimestrale OSS e versamento IVA agli Stati UE" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc20.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Verificare che le vendite B2C UE abbiano superato la soglia di 10.000€ annui; se no, si applica l'IVA italiana.",
          "Registrarsi al regime OSS sul portale dell'Agenzia delle Entrate (se non ancora fatto).",
          "Per ogni vendita B2C UE, inserire in Danea la fattura con l'aliquota IVA del paese del consumatore (es. 19% Germania, 20% Francia).",
          "Configurare in Danea le aliquote IVA estere per ogni paese UE nei Codici IVA → aggiungi nuova aliquota.",
          "Presentare la dichiarazione OSS trimestrale sul portale AdE (non tramite Danea: va fatto separatamente).",
        ],
        notes: "Danea non gestisce automaticamente il regime OSS né la dichiarazione trimestrale. Tenere un registro separato delle vendite per paese UE per compilare manualmente la dichiarazione OSS.",
      },
      {
        procedureId: proc20.id,
        erpName: "Fatture in Cloud",
        stepByStepGuide: [
          "Verificare il superamento della soglia OSS di 10.000€/anno per le vendite B2C UE.",
          "Nel piano aliquote IVA configurare le aliquote dei vari paesi UE (es. DE 19%, FR 20%, ES 21%).",
          "Per ogni vendita B2C, selezionare l'aliquota IVA corrispondente al paese del consumatore.",
          "Esportare il report vendite per paese per la dichiarazione OSS trimestrale.",
          "La dichiarazione OSS va presentata separatamente sul portale Agenzia delle Entrate entro il ultimo giorno del mese successivo al trimestre.",
        ],
        notes: "Fatture in Cloud non genera automaticamente la dichiarazione OSS. Il report 'Vendite per paese UE' è utile come base di calcolo per la compilazione manuale della dichiarazione trimestrale.",
      },
    ],
  });

  // ─── Procedure 21: Triangolazione comunitaria ────────────────────────────────
  const proc21 = await prisma.accountingProcedure.create({
    data: {
      title: "Triangolazione comunitaria – operazione con tre soggetti UE",
      normativeSummary: "Nella triangolazione comunitaria un soggetto italiano (promotore/intermediario) acquista beni da un fornitore UE (Paese A) e li rivende a un cliente in un altro Paese UE (Paese B), con consegna diretta dal fornitore al cliente finale. Il promotore italiano: (1) riceve la fattura dal fornitore con natura N3.2 (cessione intracomunitaria); (2) emette fattura verso il cliente UE con N3.2 senza IVA; (3) non è tenuto a identificarsi IVA nel Paese B grazie alla semplificazione triangolare (art. 141 Direttiva IVA). Obbligo INTRASTAT sia acquisti che cessioni.",
      electronicInvoicingFields: {
        tipo_documento: "TD18",
        natura_iva: "N3.2",
        descrizione: "Triangolazione comunitaria – acquisto intra (TD18) + cessione intra (TD01/N3.2) – art. 141 Direttiva IVA",
      },
      officialSources: [
        { source_name: "DL 331/1993 – Art. 40 c.2 (Triangolazioni comunitarie)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legge:1993-08-30;331~art40", target_paragraph: "Art. 40, comma 2 – Semplificazione per operazioni triangolari intracomunitarie" },
        { source_name: "Direttiva IVA 2006/112/CE – Art. 141 (Semplificazione triangolare)", url: "https://eur-lex.europa.eu/legal-content/IT/TXT/?uri=CELEX:32006L0112", target_paragraph: "Art. 141 – Semplificazione per operazioni triangolari: esonero dalla doppia registrazione" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc21.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Registrare l'acquisto dal fornitore UE (Paese A) con causale acquisto intra beni → genera TD18.",
          "Emettere la fattura di vendita verso il cliente UE (Paese B) con codice IVA N3.2 → tipo TD01.",
          "Nelle note della fattura di vendita indicare: 'Triangolazione comunitaria ex art. 141 Dir. 2006/112/CE – merce consegnata direttamente dal fornitore [nome fornitore/Paese A]'.",
          "Digital Hub → inviare TD18 (acquisto) e TD01/N3.2 (vendita) allo SDI.",
          "Presentare modello INTRASTAT sia INTRA-2 bis (acquisti) che INTRA-1 bis (cessioni) per il periodo.",
        ],
        notes: "Fondamentale indicare nella fattura di vendita che si tratta di una triangolazione. Il promotore italiano non deve versare IVA nel Paese B grazie alla semplificazione ex art. 141.",
      },
      {
        procedureId: proc21.id,
        erpName: "TeamSystem",
        stepByStepGuide: [
          "Registrare la fattura di acquisto intra-UE dal fornitore: causale acquisto beni UE → TD18.",
          "Emettere fattura di vendita verso il cliente UE: aliquota N3.2, tipo TD01.",
          "Inserire nella dicitura della fattura il riferimento alla triangolazione comunitaria e i dati del fornitore originario.",
          "Console SDI → inviare entrambi i documenti.",
          "Dichiarazioni Periodiche → INTRASTAT → compilare INTRA-1 bis e INTRA-2 bis per lo stesso mese.",
        ],
        notes: "TeamSystem dispone di un modulo specifico per le triangolazioni che gestisce automaticamente la doppia presentazione INTRASTAT (acquisti + cessioni) in un'unica operazione.",
      },
    ],
  });

  // ─── Procedure 22: Ritenuta su provvigioni agenti (RT02) ─────────────────────
  const proc22 = await prisma.accountingProcedure.create({
    data: {
      title: "Ritenuta su provvigioni agenti di commercio (RT02) e contributi ENASARCO",
      normativeSummary: "Le imprese mandanti devono applicare una ritenuta IRPEF del 23% sul 50% delle provvigioni corrisposte agli agenti di commercio persone fisiche (aliquota effettiva 11,5%) o 20% del 50% per agenti società. Nel tracciato XML: TipoRitenuta=RT02, AliquotaRitenuta=23.00 (o 20% per RT03), CausalePagamento=E. Separatamente, il mandante versa i contributi ENASARCO (quota agente + quota mandante) calcolati sulla provvigione lorda entro il 20 del mese successivo al trimestre.",
      electronicInvoicingFields: {
        tipo_documento: "TD01",
        natura_iva: "(aliquota IVA ordinaria 22% sulla provvigione)",
        descrizione: "Provvigione agente – RT02 23% su 50% provvigione – Causale E – contributi ENASARCO",
      },
      officialSources: [
        { source_name: "DPR 600/1973 – Art. 25-bis (Ritenute sulle provvigioni)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1973-09-29;600~art25bis", target_paragraph: "Art. 25-bis – Ritenute sulle provvigioni inerenti a rapporti di commissione, agenzia, mediazione" },
        { source_name: "ENASARCO – Regolamento contributi agenti", url: "https://www.enasarco.it/agenti-rappresentanti/contribuzione/", target_paragraph: "Contribuzione ENASARCO: aliquote, massimali, scadenze versamenti trimestrali" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc22.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Alla ricezione della fattura/nota provvigionale dall'agente, verificare l'importo della provvigione.",
          "Prima Nota → tipo documento 'PROV' → inserire la provvigione con RT02 al 23% su base 50%.",
          "Zucchetti calcola automaticamente: ritenuta = provvigione × 50% × 23%.",
          "Il netto da pagare all'agente = provvigione + IVA – ritenuta RT02.",
          "Calcolare separatamente i contributi ENASARCO: quota agente (in addebito) + quota mandante (costo aziendale).",
          "Versare ritenuta tramite F24 (codice 1038) e ENASARCO tramite bonifico entro le scadenze trimestrali.",
        ],
        notes: "Zucchetti include il modulo Agenti che calcola automaticamente ENASARCO, FIRR e FONDO INDENNITÀ su base trimestrale. Verificare i massimali annuali ENASARCO che variano di anno in anno.",
      },
      {
        procedureId: proc22.id,
        erpName: "TeamSystem",
        stepByStepGuide: [
          "Gestione Agenti → inserire o aggiornare la scheda dell'agente con i dati contrattuali.",
          "A ricezione della nota provvigionale, creare il pagamento provvigione: TeamSystem calcola RT02 e ENASARCO.",
          "Il sistema genera il prospetto ritenute (modello 770) e il prospetto ENASARCO trimestrale.",
          "Verificare nell'XML della parcella ricevuta che il blocco DatiRitenuta sia presente con TipoRitenuta=RT02.",
          "Emettere F24 per ritenuta e distinta ENASARCO per i contributi entro le scadenze.",
        ],
        notes: "TeamSystem ha un modulo specifico per la gestione agenti (provvigioni, ENASARCO, FIRR, FNASARCO) che genera automaticamente le distinte di versamento ENASARCO e il modello 770.",
      },
      {
        procedureId: proc22.id,
        erpName: "Fatture in Cloud",
        stepByStepGuide: [
          "Acquisti → registrare la fattura/nota dell'agente.",
          "Nel blocco 'Dati ritenuta' verificare che l'agente abbia configurato RT02 al 23% con causale E.",
          "Fatture in Cloud calcola il netto da pagare escludendo la ritenuta.",
          "Per ENASARCO: calcolare manualmente o con foglio di calcolo separato (Fatture in Cloud non gestisce ENASARCO nativamente).",
          "Registrare il pagamento della ritenuta tramite F24 nella sezione scadenzario.",
        ],
        notes: "Fatture in Cloud non dispone di un modulo agenti dedicato per ENASARCO: è necessario gestire separatamente i versamenti trimestrali ENASARCO con il portale ENASARCO o un software dedicato.",
      },
    ],
  });

  // ─── Procedure 23: IVA per cassa (art. 32-bis DL 83/2012) ───────────────────
  const proc23 = await prisma.accountingProcedure.create({
    data: {
      title: "Regime IVA per cassa – esigibilità differita (art. 32-bis DL 83/2012)",
      normativeSummary: "I soggetti con volume d'affari ≤ 2 milioni di euro possono optare per il regime IVA per cassa (art. 32-bis DL 83/2012): l'IVA sulle fatture emesse diventa esigibile (da versare) solo al momento del pagamento del cliente, non all'emissione. Nel tracciato XML SDI il tag <EsigibilitaIVA> deve essere impostato a 'D' (differita). Il regime non si applica a operazioni verso PA, operazioni intracomunitarie e importazioni/esportazioni.",
      electronicInvoicingFields: {
        tipo_documento: "TD01",
        natura_iva: "(aliquota ordinaria 22%) + EsigibilitaIVA = D (Differita)",
        descrizione: "Regime IVA per cassa – esigibilità differita – art. 32-bis DL 83/2012",
      },
      officialSources: [
        { source_name: "DL 83/2012 – Art. 32-bis (IVA per cassa)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legge:2012-06-22;83~art32bis", target_paragraph: "Art. 32-bis – Regime IVA per cassa per soggetti con volume d'affari non superiore a 2 milioni" },
        { source_name: "Circolare AdE 44/E del 2012 (Chiarimenti IVA per cassa)", url: "https://www.agenziaentrate.gov.it/portale/documents/20143/262513/circ_2012_044e.pdf", target_paragraph: "Paragrafo 4 – Modalità di esercizio dell'opzione e effetti sul registro IVA" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc23.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Verificare di aver esercitato l'opzione IVA per cassa nella dichiarazione IVA annuale.",
          "In Impostazioni → Opzioni Fiscali, attivare 'Regime IVA per cassa' a livello aziendale.",
          "Danea imposta automaticamente EsigibilitàIVA='D' su tutte le fatture di vendita emesse.",
          "La liquidazione IVA mensile/trimestrale considera l'IVA solo sulle fatture effettivamente incassate nel periodo.",
          "Verificare nell'XML di ogni fattura il tag <EsigibilitaIVA>D</EsigibilitaIVA>.",
        ],
        notes: "Attenzione: dopo 12 mesi dall'emissione, l'IVA diventa comunque esigibile anche se non ancora incassata (limite temporale). Danea gestisce automaticamente questa scadenza.",
      },
      {
        procedureId: proc23.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Parametri Aziendali → Opzioni IVA → attivare 'IVA per cassa ex art. 32-bis'.",
          "Zucchetti applica automaticamente EsigibilitàIVA='D' a tutte le fatture di vendita (eccetto PA e intra-UE).",
          "La liquidazione IVA periodica considera solo le fatture pagate nel periodo.",
          "Il programma monitora il limite dei 12 mesi: alla scadenza l'IVA diventa esigibile automaticamente.",
          "Verificare la corretta esclusione delle fatture PA (che richiedono EsigibilitàIVA='S' non 'D').",
        ],
        notes: "Zucchetti gestisce la coesistenza di IVA per cassa (fatture B2B con EsigibilitaIVA=D) e split payment PA (EsigibilitaIVA=S) nello stesso periodo contabile.",
      },
    ],
  });

  // ─── Procedure 24: Bonus edilizi – sconto in fattura e cessione credito ──────
  const proc24 = await prisma.accountingProcedure.create({
    data: {
      title: "Bonus edilizi – sconto in fattura e cessione del credito (Superbonus, Ecobonus, Sismabonus)",
      normativeSummary: "Le imprese edili che eseguono lavori ammessi a bonus fiscali (Superbonus 110%/90%, Ecobonus 65%, Sismabonus 85%) possono applicare uno sconto in fattura al posto del pagamento cash (art. 121 DL 34/2020). La fattura riporta il totale lavori al lordo del bonus e lo sconto applicato; l'impresa cede il credito fiscale all'intermediario finanziario. Il SAL (Stato Avanzamento Lavori) intermedio e finale devono essere certificati da tecnico abilitato e comunicati all'ENEA.",
      electronicInvoicingFields: {
        tipo_documento: "TD01",
        natura_iva: "(aliquota IVA ridotta 10% per ristrutturazioni, o 22% per nuove costruzioni)",
        descrizione: "Lavori ammessi a bonus edilizi – sconto in fattura ex art. 121 DL 34/2020",
      },
      officialSources: [
        { source_name: "DL 34/2020 – Art. 121 (Sconto in fattura e cessione credito)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legge:2020-05-19;34~art121", target_paragraph: "Art. 121 – Trasformazione delle detrazioni fiscali in sconto sul corrispettivo" },
        { source_name: "Agenzia delle Entrate – Guida bonus edilizi 2024", url: "https://www.agenziaentrate.gov.it/portale/web/guest/bonus-edilizi", target_paragraph: "Comunicazione cessione credito: termini, procedure telematiche e visto di conformità" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc24.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Creare la fattura con il totale lavori a prezzo pieno (es. 10.000€ + IVA 10% = 11.000€).",
          "Aggiungere una riga di storno/sconto con importo negativo pari allo sconto bonus (es. -7.700€ per Superbonus 90%): descrizione 'Sconto in fattura ex art. 121 DL 34/2020 – Superbonus 90%'.",
          "Il totale a pagare dal cliente sarà la differenza (es. 11.000 – 7.700 = 3.300€).",
          "Inviare allo SDI: tipo TD01 con le righe di lavori e la riga di sconto.",
          "Comunicare la cessione del credito all'Agenzia delle Entrate tramite il portale dedicato (entro il 16 marzo dell'anno successivo).",
        ],
        notes: "Il SAL (Stato Avanzamento Lavori) intermedio deve essere almeno al 30% per poter richiedere il bonus. Verificare con un tecnico abilitato prima di emettere la fattura con sconto.",
      },
      {
        procedureId: proc24.id,
        erpName: "Fatture in Cloud",
        stepByStepGuide: [
          "Fatture → Nuova Fattura → inserire le righe dei lavori con IVA al 10%.",
          "Aggiungere una riga con importo negativo: 'Sconto in fattura ex art. 121 DL 34/2020 – [tipo bonus]'.",
          "Verificare che il totale da pagare sia corretto (quota non coperta dal bonus).",
          "Emettere e inviare allo SDI.",
          "Comunicare la cessione credito sul portale AdE e ottenere il visto di conformità da un CAF/professionista abilitato.",
        ],
        notes: "Fatture in Cloud non gestisce automaticamente la comunicazione della cessione del credito all'AdE: va fatta separatamente tramite il portale dell'Agenzia delle Entrate o tramite commercialista.",
      },
    ],
  });

  // ─── Procedure 25: Credito d'imposta Transizione 4.0/5.0 ────────────────────
  const proc25 = await prisma.accountingProcedure.create({
    data: {
      title: "Credito d'imposta Transizione 4.0 / Transizione 5.0 – utilizzo in compensazione",
      normativeSummary: "Le imprese che effettuano investimenti in beni strumentali nuovi 4.0 (allegati A e B L. 232/2016) maturano un credito d'imposta utilizzabile in compensazione tramite F24. Il credito è fruibile in 3 quote annuali di pari importo a partire dall'anno di entrata in funzione del bene e previo invio della comunicazione al MISE/MIMIT (modello ministeriale). Per Transizione 5.0 (DL 19/2024): credito per investimenti in efficienza energetica e rinnovabili, comunicazione preventiva obbligatoria al GSE.",
      electronicInvoicingFields: {
        tipo_documento: "TD01",
        natura_iva: "(aliquota IVA ordinaria 22% sul bene acquistato – la fattura del fornitore è normale)",
        descrizione: "Acquisto bene strumentale 4.0/5.0 – credito d'imposta ex L. 232/2016 / DL 19/2024 – comunicazione MIMIT/GSE",
      },
      officialSources: [
        { source_name: "Legge 232/2016 (Budget Law) – Industria 4.0", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:legge:2016-12-11;232", target_paragraph: "Art. 1, commi 9-13 – Credito d'imposta beni strumentali nuovi 4.0 (Allegati A e B)" },
        { source_name: "MIMIT – Comunicazione investimenti 4.0 (modello e istruzioni)", url: "https://www.mise.gov.it/index.php/it/incentivi/impresa/transizione-40", target_paragraph: "Modello di comunicazione obbligatoria per il credito d'imposta beni materiali/immateriali 4.0" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc25.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Alla ricezione della fattura del fornitore per il bene 4.0, registrarla normalmente in Prima Nota.",
          "Nel cespite (Gestione Cespiti), classificare il bene come 'Allegato A 4.0' e annotare il valore dell'investimento.",
          "Dopo l'entrata in funzione del bene e l'invio della comunicazione MIMIT, calcolare il credito d'imposta spettante.",
          "Creare nel piano dei conti il conto 'Credito d'imposta 4.0' (attivo patrimoniale).",
          "In F24 → Compensazione, utilizzare il credito con codice tributo 6936 (beni materiali) o 6937 (immateriali).",
        ],
        notes: "Il credito si utilizza in 3 quote annuali. Verificare con il consulente fiscale il corretto calcolo delle percentuali (le aliquote variano per valore investimento e anno).",
      },
      {
        procedureId: proc25.id,
        erpName: "TeamSystem",
        stepByStepGuide: [
          "Registrare la fattura di acquisto del bene strumentale normalmente.",
          "Gestione Cespiti → creare il cespite con categoria '4.0' e inserire data entrata in funzione.",
          "TeamSystem calcola automaticamente le quote annuali del credito d'imposta spettante.",
          "Gestione Crediti Imposta → inserire il credito con codice tributo 6936 o 6937 per l'utilizzo in F24.",
          "Compensare il credito nelle scadenze F24 mensili (il credito è utilizzabile dall'anno successivo all'entrata in funzione).",
        ],
        notes: "TeamSystem include un modulo specifico per i crediti d'imposta 4.0 che tiene traccia dell'ammontare maturato, dell'importo già utilizzato e del residuo disponibile per anno.",
      },
    ],
  });

  // ─── Procedure 26: Cassa professionale e rivalsa (4% CNPAF, 2% Cassa Forense)
  const proc26 = await prisma.accountingProcedure.create({
    data: {
      title: "Rivalsa contributo integrativo cassa professionale (4% CNPAF, 2% Cassa Forense, ecc.)",
      normativeSummary: "I professionisti iscritti a casse previdenziali di categoria (commercialisti CNPAF 4%, avvocati Cassa Forense 4%, ingegneri/architetti INARCASSA 4%, ecc.) addebitano al cliente una rivalsa del contributo integrativo sull'imponibile della prestazione. La rivalsa non è soggetta a IVA se è a titolo di rimborso spese (art. 15 DPR 633/72), ma nella prassi comune si assoggetta a IVA per semplificare. Il contributo integrativo riportato in fattura è deducibile per il committente ma non riduce la base imponibile IRPEF del professionista.",
      electronicInvoicingFields: {
        tipo_documento: "TD01",
        natura_iva: "(aliquota ordinaria 22% su tutto l'imponibile inclusa la rivalsa)",
        descrizione: "Rivalsa contributo integrativo 4% CNPAF / 2% Cassa Forense – art. 1 c.212 L. 662/1996",
      },
      officialSources: [
        { source_name: "CNPAF – Contributo integrativo 4% (commercialisti)", url: "https://www.cnpadc.it/", target_paragraph: "Art. 8 Statuto CNPAF – Contributo integrativo del 4% su tutti i corrispettivi" },
        { source_name: "Cassa Forense – Contributo integrativo 4% (avvocati)", url: "https://www.cassaforense.it/", target_paragraph: "Contributo integrativo 4% su tutti i corrispettivi – addebitabile in rivalsa al cliente" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc26.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Creare le righe della fattura per la prestazione professionale con IVA 22%.",
          "Aggiungere una riga separata: 'Contributo integrativo CNPAF 4% ex L.662/96' = imponibile × 4%.",
          "Applicare IVA 22% anche sulla riga della rivalsa (prassi comune per semplicità).",
          "Verificare: Imponibile = onorario + rivalsa; IVA = (onorario + rivalsa) × 22%; Ritenuta = onorario × 20%.",
          "Inviare allo SDI tipo TD01.",
        ],
        notes: "Il contributo integrativo va versato alla propria cassa di appartenenza con le modalità previste. La ritenuta d'acconto (20%) si calcola solo sull'onorario, non sulla rivalsa.",
      },
      {
        procedureId: proc26.id,
        erpName: "Fatture in Cloud",
        stepByStepGuide: [
          "Fatture → Nuova → inserire le righe del compenso professionale con IVA 22%.",
          "Aggiungere una riga per la rivalsa cassa professionale (es. 4% CNPAF) con IVA 22%.",
          "Impostare la ritenuta d'acconto RT01 al 20% solo sull'onorario (escludere la rivalsa dalla base della ritenuta).",
          "Calcolo finale: Totale = (onorario + rivalsa) + IVA su entrambi – ritenuta solo su onorario.",
          "Inviare allo SDI.",
        ],
        notes: "Fatture in Cloud permette di escludere singole righe dalla base di calcolo della ritenuta d'acconto: impostare la riga della rivalsa come 'esclusa da ritenuta'.",
      },
    ],
  });

  // ─── Procedure 27: Acquisto beni strumentali con plus/minusvalenza ───────────
  const proc27 = await prisma.accountingProcedure.create({
    data: {
      title: "Cessione beni strumentali – plusvalenza o minusvalenza",
      normativeSummary: "La vendita di beni strumentali d'impresa (automezzi, macchinari, attrezzature, fabbricati d'impresa) genera una plusvalenza (ricavo > valore residuo) o minusvalenza (ricavo < valore residuo) fiscalmente rilevante. La fattura di vendita è soggetta a IVA ordinaria. La plusvalenza è imponibile IRES/IRPEF (con eventuale rateazione quinquennale se il bene è detenuto da più di 3 anni). La minusvalenza è deducibile nell'esercizio di realizzo.",
      electronicInvoicingFields: {
        tipo_documento: "TD01",
        natura_iva: "(aliquota ordinaria 22% sul prezzo di vendita del bene strumentale)",
        descrizione: "Cessione bene strumentale con plusvalenza/minusvalenza – art. 86-87 TUIR",
      },
      officialSources: [
        { source_name: "TUIR – Art. 86-87 (Plusvalenze patrimoniali d'impresa)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.del.presidente.della.repubblica:1986-12-22;917~art86", target_paragraph: "Art. 86 – Plusvalenze patrimoniali: imponibilità, rateazione e cessione in corso d'anno" },
        { source_name: "TUIR – Art. 101 (Minusvalenze patrimoniali)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.del.presidente.della.repubblica:1986-12-22;917~art101", target_paragraph: "Art. 101 – Deducibilità delle minusvalenze nell'esercizio di realizzo" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc27.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Gestione Cespiti → aprire la scheda del bene da cedere e verificare il valore residuo netto.",
          "Emettere la fattura di vendita dal modulo Fatturazione Attiva con IVA 22% sul prezzo di vendita.",
          "Il programma calcola automaticamente plusvalenza o minusvalenza: prezzo vendita – valore residuo = plus/minus.",
          "Contabilizzare la cessione del cespite: il sistema storna il fondo ammortamento e il valore originale.",
          "Per plusvalenza: configurare la rateazione quinquennale se il bene era posseduto da >3 anni.",
        ],
        notes: "Zucchetti gestisce automaticamente la rateazione quinquennale della plusvalenza nei parametri del cespite. Ricordare di segnalare la plusvalenza in dichiarazione dei redditi (quadro RF/RG).",
      },
      {
        procedureId: proc27.id,
        erpName: "TeamSystem",
        stepByStepGuide: [
          "Gestione Cespiti → scheda del bene → Cessione → inserire il prezzo di vendita.",
          "TeamSystem calcola automaticamente la plusvalenza/minusvalenza confrontando il prezzo con il valore netto residuo.",
          "Emettere la fattura di vendita con IVA 22% dalla Fatturazione Attiva.",
          "Il sistema genera automaticamente la registrazione contabile di dismissione del cespite.",
          "Verificare il trattamento fiscale della plusvalenza e l'eventuale opzione per la rateazione quinquennale.",
        ],
        notes: "TeamSystem include la stampa del 'Prospetto dismissione cespiti' con il calcolo della plus/minusvalenza per la dichiarazione dei redditi.",
      },
    ],
  });

  // ─── Procedure 28: Locazione immobiliare con opzione IVA ────────────────────
  const proc28 = await prisma.accountingProcedure.create({
    data: {
      title: "Locazione immobile strumentale con opzione IVA (art. 10 n.8 DPR 633/72)",
      normativeSummary: "Le locazioni di fabbricati strumentali sono di norma esenti IVA (art. 10 n.8 DPR 633/72), ma il locatore può optare per l'applicazione dell'IVA al 22% se il conduttore non ha diritto alla detrazione IVA o ha un pro-rata basso. L'opzione si esercita nell'atto di locazione o con dichiarazione separata. La fattura mensile del canone riporta quindi IVA 22% anziché l'esenzione N1.",
      electronicInvoicingFields: {
        tipo_documento: "TD01",
        natura_iva: "(22% se opzione IVA esercitata, oppure N1 se esente – verificare il contratto)",
        descrizione: "Canone locazione immobile strumentale con opzione IVA 22% – art. 10 n.8-ter DPR 633/72",
      },
      officialSources: [
        { source_name: "DPR 633/1972 – Art. 10, n.8 e 8-ter (Locazioni immobili)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633~art10", target_paragraph: "Art. 10, n.8 (fabbricati residenziali esenti) e n.8-ter (strumentali con opzione IVA)" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc28.id,
        erpName: "Fatture in Cloud",
        stepByStepGuide: [
          "Verificare nel contratto di locazione se è stata esercitata l'opzione IVA.",
          "Se opzione IVA attiva: creare la fattura mensile del canone con aliquota 22%.",
          "Se non attiva: creare la fattura con natura N1 (esente art. 10).",
          "Nella descrizione inserire: 'Canone di locazione [mese/anno] – immobile sito in [indirizzo] – contratto [n. rep/data]'.",
          "Inviare allo SDI tipo TD01.",
        ],
        notes: "Ricordare di registrare il contratto di locazione presso l'Agenzia delle Entrate (se non già telematicamente) e versare l'imposta di registro annualmente. Il canone è soggetto a ritenuta d'acconto del 20% se il locatario è un sostituto d'imposta.",
      },
      {
        procedureId: proc28.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Configurare il contratto di locazione nell'apposito modulo con data, canone e opzione IVA.",
          "Fatturazione Attiva → Fatture Ricorrenti → Zucchetti genera automaticamente la fattura mensile del canone.",
          "La fattura usa l'aliquota 22% (se opzione IVA) o N1 (se esente) in base alle impostazioni del contratto.",
          "Digital Hub → inviare allo SDI entro la data di scadenza del canone (tipicamente il 1° del mese).",
        ],
        notes: "Zucchetti supporta la generazione automatica di fatture ricorrenti per i canoni di locazione: una volta configurato il contratto, le fatture mensili vengono generate senza intervento manuale.",
      },
    ],
  });

  // ─── Procedure 29: Operazioni fuori campo IVA (art. 7 DPR 633/72) ───────────
  const proc29 = await prisma.accountingProcedure.create({
    data: {
      title: "Operazioni fuori campo IVA – territorialità (art. 7 DPR 633/72)",
      normativeSummary: "Le prestazioni di servizi rese a soggetti passivi IVA stabiliti fuori dall'UE (art. 7-ter DPR 633/72) o alcune cessioni di beni non territorialmente rilevanti in Italia sono fuori dal campo di applicazione dell'IVA italiana. La fattura va emessa senza IVA con natura N2.1 (non soggette – artt. 7 a 7-septies) e con la dicitura 'Operazione fuori campo IVA'. Non vengono inserite nel registro IVA ma concorrono al volume d'affari.",
      electronicInvoicingFields: {
        tipo_documento: "TD01",
        natura_iva: "N2.1",
        descrizione: "Fuori campo IVA – non soggetta per mancanza del presupposto territoriale – art. 7-ter DPR 633/72",
      },
      officialSources: [
        { source_name: "DPR 633/1972 – Art. 7-ter (Territorialità servizi B2B)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633~art7ter", target_paragraph: "Art. 7-ter – Luogo delle prestazioni di servizi generiche: paese del committente per B2B" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc29.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Creare la fattura selezionando il cliente extra-UE (paese terzo).",
          "Per ogni riga di servizio, selezionare 'Fuori campo IVA – N2.1'.",
          "Aggiungere la dicitura: 'Operazione non soggetta ad IVA ai sensi dell'art. 7-ter DPR 633/72'.",
          "Verificare nell'XML il tag <Natura>N2.1</Natura>.",
          "Inviare allo SDI: la fattura è comunque obbligatoria allo SDI anche se fuori campo IVA.",
        ],
        notes: "N2.1 (fuori campo per territorialità) è diverso da N1 (esente) e N2.2 (regime forfettario). Verificare sempre il corretto codice natura per evitare errori nella liquidazione IVA.",
      },
      {
        procedureId: proc29.id,
        erpName: "Fatture in Cloud",
        stepByStepGuide: [
          "Selezionare il cliente extra-UE nell'anagrafica.",
          "Per le righe del servizio, impostare aliquota 'N2.1 – Non soggetta art. 7-ter'.",
          "Fatture in Cloud propone automaticamente N2.1 per clienti extra-UE soggetti passivi.",
          "Inviare allo SDI.",
        ],
        notes: "Per i servizi resi a privati (B2C) extra-UE si applicano regole diverse: verificare la normativa specifica per la tipologia di servizio (es. servizi elettronici = OSS).",
      },
    ],
  });

  // ─── Procedure 30: Regime speciale agricoltura (art. 34 DPR 633/72) ──────────
  const proc30 = await prisma.accountingProcedure.create({
    data: {
      title: "Fatturazione in regime speciale agricoltura (art. 34 DPR 633/72)",
      normativeSummary: "I produttori agricoli con volume d'affari ≤ 7.000€ sono esonerati dagli obblighi IVA (art. 34 c.6). I produttori con volume >7.000€ applicano il regime speciale: l'IVA dovuta è determinata dalla differenza tra l'IVA incassata (aliquota di cessione) e l'IVA compensata (percentuale di compensazione fissa per prodotto). Non si effettua liquidazione IVA analitica: si versa la differenza o si porta a credito. L'IVA sulle fatture emesse usa le aliquote previste dalla tabella A/I DPR 633/72.",
      electronicInvoicingFields: {
        tipo_documento: "TD01",
        natura_iva: "(4%, 10% o 22% secondo la tabella A/I per i prodotti agricoli ceduti)",
        descrizione: "Cessione prodotti agricoli – regime speciale art. 34 DPR 633/72 – percentuale compensazione",
      },
      officialSources: [
        { source_name: "DPR 633/1972 – Art. 34 (Regime speciale per produttori agricoli)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633~art34", target_paragraph: "Art. 34 – Regime speciale per i produttori agricoli: percentuali di compensazione e adempimenti" },
        { source_name: "DPR 633/1972 – Tabella A Parte I (Prodotti agricoli IVA 4%)", url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633", target_paragraph: "Tabella A, Parte I – Beni e servizi soggetti all'aliquota del 4% per i produttori agricoli" },
      ],
    },
  });

  await prisma.erpMapping.createMany({
    data: [
      {
        procedureId: proc30.id,
        erpName: "Danea Easyfatt",
        stepByStepGuide: [
          "Configurare in Impostazioni → Regime IVA: selezionare 'Regime Speciale Agricoltura art. 34'.",
          "Creare i codici IVA per i prodotti agricoli (4%, 10%) secondo la tabella A/I.",
          "Emettere le fatture di vendita con le aliquote corrispondenti ai prodotti ceduti.",
          "La liquidazione IVA periodica calcolerà la differenza tra IVA incassata e percentuale di compensazione.",
          "Inviare allo SDI tipo TD01 con le aliquote corrette.",
        ],
        notes: "Danea permette di configurare le percentuali di compensazione per prodotto agricolo. Aggiornare periodicamente le percentuali se modificate da decreto ministeriale.",
      },
      {
        procedureId: proc30.id,
        erpName: "Zucchetti Mago/Adhoc",
        stepByStepGuide: [
          "Parametri Aziendali → attivare 'Regime Speciale IVA Agricoltura art. 34'.",
          "Configurare nel piano IVA le aliquote e le percentuali di compensazione per categoria di prodotto.",
          "Emettere le fatture con le aliquote della tabella A/I.",
          "Zucchetti calcola automaticamente il saldo IVA come differenza tra aliquota di cessione e percentuale di compensazione.",
          "Digital Hub → inviare le fatture allo SDI.",
        ],
        notes: "Zucchetti include un report specifico per il regime speciale agricoltura che calcola il saldo IVA annuale tenendo conto delle percentuali di compensazione per categoria merceologica.",
      },
    ],
  });

  console.log("Seeding completed successfully! Created 30 procedures with all ERP mappings.");
}

main()
  .catch((e) => {
    console.error("Error during seed:", e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
