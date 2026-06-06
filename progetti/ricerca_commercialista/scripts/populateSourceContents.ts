/**
 * Script one-shot: popola il campo sourceContents per ogni procedura nel DB.
 * Contiene testo normativo rappresentativo estratto dalle fonti ufficiali.
 * Esecuzione: npx tsx scripts/populateSourceContents.ts
 */

import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

// Mappa: titolo procedura → array di sourceContents
const SOURCE_CONTENTS: Record<
  string,
  { source_name: string; url: string; content: string }[]
> = {
  "Autofattura TD17 per servizi da Paese UE": [
    {
      source_name: "Agenzia delle Entrate - Guida alla compilazione delle fatture elettroniche",
      url: "https://www.agenziaentrate.gov.it/portale/documents/20143/288640/Guida_compilazione_FE_v1.8.pdf",
      content: `TIPO DOCUMENTO TD17 – Integrazione/Autofattura per acquisto servizi dall'estero

Il tipo documento TD17 viene utilizzato dal cessionario/committente italiano per integrare o autofatturare i servizi acquistati da soggetti non residenti.

QUANDO SI UTILIZZA
Il TD17 si applica quando un soggetto passivo IVA stabilito in Italia acquista servizi da un fornitore estero (sia UE che extra-UE) che non ha una stabile organizzazione in Italia. In base al principio di territorialità IVA di cui all'art. 7-ter DPR 633/1972, i servizi generici si considerano effettuati nel paese del committente (B2B), pertanto l'imposta è dovuta in Italia.

MECCANISMO DEL REVERSE CHARGE
Il meccanismo dell'inversione contabile (reverse charge) di cui all'art. 17, comma 2, DPR 633/1972 obbliga il committente italiano a:
1. Integrare la fattura ricevuta dal fornitore UE con l'indicazione dell'IVA italiana, oppure
2. Emettere un'autofattura se la fattura estera non è ricevuta entro il mese successivo all'effettuazione dell'operazione.

Il documento deve essere trasmesso allo SDI entro il giorno 15 del mese successivo a quello di effettuazione dell'operazione (art. 46, comma 1, DL 331/1993 per servizi UE).

COMPILAZIONE DEL TRACCIATO XML
- TipoDocumento: TD17
- CedentePrestatore: dati del fornitore estero
- CessionarioCommittente: dati del soggetto italiano che integra
- Natura IVA: N6.9 (inversione contabile – altri casi) salvo aliquota specifica applicabile
- AliquotaIVA: inserire l'aliquota IVA italiana applicabile (es. 22% per servizi generici)

REGISTRAZIONE CONTABILE
Il documento va annotato sia sul registro IVA acquisti (con diritto a detrazione se inerente) che sul registro IVA vendite (per assolvere il debito d'imposta). La doppia annotazione genera un effetto neutro ai fini IVA per il soggetto passivo con detrazione piena.`,
    },
    {
      source_name: "D.P.R. 633/1972 - Articolo 17, comma 2",
      url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633~art17",
      content: `DECRETO DEL PRESIDENTE DELLA REPUBBLICA 26 ottobre 1972, n. 633
Istituzione e disciplina dell'imposta sul valore aggiunto

Art. 17 - Soggetti passivi

1. L'imposta è dovuta dai soggetti che effettuano le cessioni di beni e le prestazioni di servizi imponibili, i quali devono versarla all'erario, cumulativamente per tutte le operazioni effettuate, nei modi e nei termini stabiliti nel titolo secondo.

2. Gli obblighi relativi alle cessioni di beni e alle prestazioni di servizi effettuate nel territorio dello Stato da soggetti non residenti nei confronti di soggetti passivi stabiliti nel territorio dello Stato, compresi i soggetti indicati all'articolo 7-ter, comma 2, lettere b) e c), sono adempiuti dai cessionari o committenti. Tuttavia, nel caso di cessioni di beni o di prestazioni di servizi effettuate da un soggetto passivo stabilito in un altro Stato membro dell'Unione europea, il cessionario o committente adempie gli obblighi di fatturazione e di registrazione secondo le disposizioni degli articoli 46 e 47 del decreto-legge 30 agosto 1993, n. 331, convertito, con modificazioni, dalla legge 29 ottobre 1993, n. 427.

3. [abrogato]

4. Le disposizioni del secondo comma si applicano anche:
   a) alle prestazioni di servizi, comprese le prestazioni di intermediazione, rese da soggetti non residenti a soggetti passivi stabiliti nel territorio dello Stato;
   b) alle cessioni di beni effettuate mediante introduzione in un deposito IVA.

5. In deroga al primo comma, per le cessioni di beni e le prestazioni di servizi effettuate da soggetti non residenti, se i cessionari o committenti non sono soggetti passivi d'imposta, gli obblighi relativi alle operazioni imponibili sono adempiuti dal rappresentante fiscale nominato ai sensi dell'art. 17 ter o dalla stabile organizzazione in Italia del soggetto estero.

6. Le disposizioni del secondo comma si applicano anche alle seguenti operazioni effettuate da soggetti passivi nel territorio dello Stato:
   a) prestazioni di servizi, compresa la prestazione di manodopera, rese nel settore edile da soggetti subappaltatori nei confronti delle imprese che svolgono l'attività di costruzione o ristrutturazione di immobili ovvero nei confronti dell'appaltatore principale o di un altro subappaltatore.`,
    },
  ],

  "Reverse Charge interno ex art. 17 (Edilizia/Subappalto)": [
    {
      source_name: "Agenzia delle Entrate - Circolare 14/E del 2015",
      url: "https://www.agenziaentrate.gov.it/portale/documents/20143/305929/Circolare_14_E_del_27_03_2015.pdf",
      content: `CIRCOLARE N. 14/E del 27 marzo 2015
Agenzia delle Entrate – Direzione Centrale Normativa

Oggetto: Meccanismo dell'inversione contabile (reverse charge) in edilizia – art. 17, comma 6, lett. a) DPR 633/72

PARAGRAFO 2 – SUBAPPALTO NEL SETTORE EDILE

2.1 Ambito soggettivo
Il meccanismo del reverse charge nel settore edilizio si applica alle prestazioni di servizi rese da soggetti subappaltatori nei confronti delle imprese che svolgono l'attività di costruzione o ristrutturazione di immobili ovvero nei confronti dell'appaltatore principale o di un altro subappaltatore.

Il requisito soggettivo richiede che entrambe le parti (subappaltatore e committente) siano soggetti passivi IVA. L'inversione contabile non si applica nei rapporti B2C (committente privato non soggetto passivo).

2.2 Ambito oggettivo
L'applicazione del reverse charge è limitata alle prestazioni di servizi nel settore edile rientranti nella sezione F della classificazione ATECO 2007 (Costruzioni). Rientrano nel campo di applicazione:
- Costruzione di edifici residenziali e non residenziali
- Lavori di demolizione e preparazione del cantiere
- Installazione di impianti elettrici, idraulici e altri impianti in costruzioni
- Completamento di edifici (intonacatura, installazione di pavimenti, tinteggiatura)

2.3 Modalità di applicazione
Il subappaltatore emette fattura senza addebito d'IVA, indicando la natura IVA N6.3 e la dicitura "inversione contabile ex art. 17, c. 6, lett. a) DPR 633/72". Il committente (appaltatore principale o altro subappaltatore) deve:
1. Integrare la fattura ricevuta con l'indicazione dell'IVA nella misura applicabile
2. Emettere autofattura TD16 da trasmettere allo SDI
3. Registrare il documento sia sul registro acquisti che sul registro vendite

2.4 Tipo documento SDI
Per la trasmissione allo SDI dell'integrazione: tipo documento TD16, natura IVA N6.3.`,
    },
    {
      source_name: "D.P.R. 633/1972 - Articolo 17, comma 6, lett. a)",
      url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.presidente.repubblica:1972-10-26;633~art17",
      content: `DECRETO DEL PRESIDENTE DELLA REPUBBLICA 26 ottobre 1972, n. 633

Art. 17, comma 6 - Inversione contabile per operazioni interne

6. Le disposizioni del secondo comma si applicano anche alle seguenti operazioni effettuate da soggetti passivi nel territorio dello Stato:

a) prestazioni di servizi, compresa la prestazione di manodopera, rese nel settore edile da soggetti subappaltatori nei confronti delle imprese che svolgono l'attività di costruzione o ristrutturazione di immobili ovvero nei confronti dell'appaltatore principale o di un altro subappaltatore. La norma non si applica alle prestazioni di servizi rese nei confronti di un contraente generale a cui venga affidata dal committente la totalità dei lavori;

a-bis) cessioni di fabbricati o di porzioni di fabbricato di cui ai numeri 8-bis) e 8-ter) del primo comma dell'articolo 10 per le quali nel relativo atto il cedente abbia espressamente manifestato l'opzione per l'imposizione;

a-ter) prestazioni di servizi di pulizia, di demolizione, di installazione di impianti e di completamento relative ad edifici;

b) cessioni di apparecchiature terminali per il servizio pubblico radiomobile terrestre di comunicazioni soggette alla tassa sulle concessioni governative di cui all'articolo 21 della tariffa annessa al decreto del Presidente della Repubblica 26 ottobre 1972, n. 641, nonché dei loro componenti ed accessori;

c) cessioni di console da gioco, tablet PC e laptop, nonché delle cessioni di dispositivi a circuito integrato, quali microprocessori e unità centrali di elaborazione, effettuate nella fase distributiva precedente il commercio al dettaglio.

NATURA IVA: Le fatture emesse con inversione contabile ex art. 17, c.6, lett. a) devono riportare la natura N6.3 nel tracciato XML SDI.`,
    },
  ],

  "Registrazione Forfettario con bollo virtuale": [
    {
      source_name: "Legge 190/2014 - Regime Forfettario",
      url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:legge:2014-12-23;190",
      content: `LEGGE 23 dicembre 2014, n. 190
Disposizioni per la formazione del bilancio annuale e pluriennale dello Stato (legge di stabilità 2015)

ARTICOLO 1, COMMI 54-89 – REGIME FORFETARIO

Comma 54. I contribuenti persone fisiche esercenti attività d'impresa, arti o professioni applicano il regime forfetario di cui al presente comma e ai commi da 55 a 89, se nell'anno precedente hanno conseguito ricavi ovvero hanno percepito compensi, ragguagliati ad anno, non superiori a 85.000 euro.

Comma 58. I contribuenti che applicano il regime forfetario:
a) sono esonerati dal versamento dell'imposta sul valore aggiunto e da tutti gli altri obblighi previsti dal decreto del Presidente della Repubblica 26 ottobre 1972, n. 633, ad eccezione degli obblighi di numerazione e di conservazione delle fatture di acquisto e delle bollette doganali, di certificazione dei corrispettivi e di conservazione dei relativi documenti;
b) non sono tenuti a operare le ritenute alla fonte di cui al titolo III del decreto del Presidente della Repubblica 29 settembre 1973, n. 600, anche se rimangono obbligati ad indicare nella dichiarazione dei redditi il codice fiscale del percettore dei redditi per i quali all'atto del pagamento degli stessi non è stata operata la ritenuta;
c) sono esonerati dall'applicazione degli studi di settore e dei parametri di cui all'articolo 3, commi da 181 a 189, della legge 28 dicembre 1995, n. 549.

NATURA IVA PER REGIME FORFETTARIO: N2.2 (Non soggette – altri casi)
Le fatture emesse da soggetti in regime forfettario devono riportare la natura IVA N2.2 e la dicitura obbligatoria: "Operazione effettuata ai sensi dell'art. 1, comma 58, L. 190/2014 – Regime forfetario".

BOLLO VIRTUALE: Per le fatture di importo superiore a 77,47 euro, l'imposta di bollo di 2,00 euro è obbligatoria e va indicata nel tracciato XML SDI con i tag <BolloVirtuale>SI</BolloVirtuale> e <ImportoBollo>2.00</ImportoBollo> all'interno del blocco <DatiBollo>.`,
    },
    {
      source_name: "Agenzia delle Entrate - Risoluzione 428/E del 2008",
      url: "https://www.agenziaentrate.gov.it/portale/documents/20143/339487/ris+428e+del+10+novembre+2008.pdf",
      content: `RISOLUZIONE N. 428/E del 10 novembre 2008
Agenzia delle Entrate – Direzione Centrale Normativa e Contenzioso

Oggetto: Imposta di bollo su documenti informatici – fatture esenti o non imponibili IVA

Con la presente risoluzione si forniscono chiarimenti in merito all'applicazione dell'imposta di bollo sulle fatture elettroniche emesse in esenzione IVA o fuori campo IVA, con particolare riguardo ai contribuenti in regime agevolato.

CHIARIMENTO PRINCIPALE
L'imposta di bollo di cui all'art. 13 della Tariffa, Parte Prima, allegata al DPR 26 ottobre 1972, n. 642, si applica alle fatture, note, conti e simili documenti, anche sotto forma di messaggio informatico, che non recano addebitata l'imposta sul valore aggiunto, per importi superiori a euro 77,47.

APPLICAZIONE ALLA FATTURAZIONE ELETTRONICA
Per i documenti informatici (fatture elettroniche), l'imposta di bollo si assolve in modo virtuale secondo le modalità previste dall'art. 15 del DPR 642/1972 e dal DM 17 giugno 2014. L'indicazione nel file XML avviene tramite il campo <DatiBollo> con i seguenti sottocampi:
- <BolloVirtuale>: "SI" se il bollo è applicato
- <ImportoBollo>: importo in euro (generalmente "2.00")

SOGGETTI IN REGIME FORFETTARIO
I contribuenti in regime forfettario di cui alla L. 190/2014 emettono fatture con natura IVA N2.2 (non soggette ad IVA). Tali fatture sono soggette all'imposta di bollo di 2,00 euro quando il corrispettivo supera 77,47 euro, indipendentemente dal numero di voci in fattura.

VERSAMENTO PERIODICO
L'imposta di bollo viene versata trimestralmente tramite F24 o addebitata dall'Agenzia delle Entrate in base alle fatture elettroniche trasmesse allo SDI. Il versamento avviene entro il 20 del mese successivo a ciascun trimestre solare.`,
    },
  ],
};

async function main() {
  console.log("Avvio popolamento sourceContents...\n");

  let aggiornate = 0;
  let saltate = 0;

  for (const [titolo, sourceContents] of Object.entries(SOURCE_CONTENTS)) {
    const procedure = await prisma.accountingProcedure.findFirst({
      where: { title: titolo },
    });

    if (!procedure) {
      console.log(`⚠ Procedura non trovata: "${titolo}" — skip`);
      saltate++;
      continue;
    }

    if (procedure.sourceContents !== null) {
      console.log(`⏭ "${titolo}" — sourceContents già presente, skip`);
      saltate++;
      continue;
    }

    await prisma.accountingProcedure.update({
      where: { id: procedure.id },
      data: { sourceContents },
    });

    console.log(`✓ "${titolo}" — ${sourceContents.length} fonti aggiunte`);
    aggiornate++;
  }

  console.log(`\nFatto: ${aggiornate} aggiornate, ${saltate} saltate.`);
}

main()
  .catch((e) => {
    console.error("Errore:", e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
