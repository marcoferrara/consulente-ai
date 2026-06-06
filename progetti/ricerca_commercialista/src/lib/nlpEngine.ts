/**
 * NLP Semantic & Keyword Search Engine for LexDocs
 * Implements Italian tokenization, stopwords stripping, specialized accounting synonym dictionary,
 * fuzzy matching (Levenshtein Distance) and score ranking.
 */

// 1. Italian Stopwords List
const ITALIAN_STOPWORDS = new Set([
  "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "di", "del", "dello", "della",
  "dei", "degli", "delle", "a", "al", "allo", "alla", "ai", "agli", "alle", "da", "dal",
  "dallo", "dalla", "dai", "dagli", "dalle", "in", "nel", "nello", "nella", "nei", "negli",
  "nelle", "con", "col", "su", "sul", "sullo", "sulla", "sui", "sugli", "sulle", "per",
  "tra", "fra", "e", "ed", "o", "ma", "come", "che", "chi", "cui", "non", "sono", "con la"
]);

// 2. Specialized Accounting Synonym / Intent Dictionary
// Keys represent intent categories, values contain lists of words associated with that intent
interface IntentDefinition {
  id: string;
  titleKeyword: string; // keyword expected in the procedure title
  synonyms: string[];
  intentLabel: string;
}

const INTENT_DICTIONARY: IntentDefinition[] = [
  {
    id: "TD17",
    titleKeyword: "TD17",
    synonyms: [
      // Nomi di paese rimossi: "Francia/franca" causava falsi positivi con "zona franca"
      "ue", "cee", "estero", "comunitario", "intracomunitario", "europa",
      "vies", "servizi esteri", "servizi ue", "fuori cee", "import"
    ],
    intentLabel: "Integrazione/Autofattura UE (TD17) per servizi esteri"
  },
  {
    id: "TD16",
    titleKeyword: "TD16",
    synonyms: [
      "reverse", "charge", "inversione", "contabile", "edilizia", "subappalto", "costruzioni",
      "cantiere", "art 17", "art.17", "quadro re", "appalto", "edili"
    ],
    intentLabel: "Reverse Charge interno ex Art. 17 (TD16) per Edilizia"
  },
  {
    id: "TD01",
    titleKeyword: "Forfettario",
    synonyms: [
      "forfettario", "forfetario", "minimi", "esente iva", "bollo", "virtuale", "marca",
      "marca da bollo", "77", "77 euro", "flat tax", "agevolato", "n2.2"
    ],
    intentLabel: "Fatturazione Regime Forfettario con bollo virtuale"
  },
  {
    id: "ZonaFranca",
    titleKeyword: "Zona Franca",
    synonyms: [
      "zona", "franca", "franco", "zes", "porto franco", "porto", "deposito doganale",
      "doganale", "dogana", "zona economica", "speciale", "zfu", "zona franca urbana",
      "n3", "n3.4", "lettera intento", "lettera", "intento", "dichiarazione intento",
      "esportatore", "esportatori", "abituale", "abituali", "plafond", "non imponibile",
      "art 8", "art.8", "sospensione"
    ],
    intentLabel: "Fatturazione a soggetto in Zona Franca / ZES (N3.4 – Lettera d'intento)"
  },
  {
    id: "TD04",
    titleKeyword: "Nota di Credito",
    synonyms: [
      "nota", "credito", "td04", "storno", "storni", "rettifica", "rettifiche",
      "annullamento", "variazione", "rimborso", "accredito", "art 26", "art.26"
    ],
    intentLabel: "Nota di Credito (TD04) – Storno o rettifica fattura"
  },
  {
    id: "SplitPayment",
    titleKeyword: "Split Payment",
    synonyms: [
      "split", "payment", "scissione", "pagamenti", "pubblica", "amministrazione",
      "pa", "ente", "pubblico", "pubblici", "comune", "regione", "asl", "università",
      "17ter", "art 17ter", "esigibilita", "mef", "cuu", "ipa", "codice univoco"
    ],
    intentLabel: "Split Payment – Scissione dei Pagamenti (fattura a PA)"
  },
  {
    id: "Ritenuta",
    titleKeyword: "ritenuta",
    synonyms: [
      "ritenuta", "acconto", "irpef", "professionale", "professionista", "compenso",
      "parcella", "rt01", "rt02", "20%", "sostituto", "imposta", "cud", "cu",
      "certificazione", "unica", "lavoro", "autonomo", "art 25", "art.25"
    ],
    intentLabel: "Compenso professionale con ritenuta d'acconto (RT01 – 20% IRPEF)"
  },
  {
    id: "CessioneIntraUE",
    titleKeyword: "cessione intracomunitaria",
    synonyms: [
      "cessione", "intracomunitaria", "n3.2", "vendita", "beni", "ue", "cliente",
      "comunitario", "intrastat", "intra", "vies", "cmr", "trasporto", "art 41",
      "dl 331", "331", "spedizione", "esportazione", "europa"
    ],
    intentLabel: "Cessione intracomunitaria di beni a soggetto UE (N3.2)"
  },
  {
    id: "TD18",
    titleKeyword: "TD18",
    synonyms: [
      "td18", "acquisto", "beni", "intracomunitari", "intra", "ue", "cee",
      "fornitore", "estero", "merci", "merci ue", "acquisto intra"
    ],
    intentLabel: "Integrazione acquisto beni intracomunitari (TD18)"
  },
  {
    id: "TD19",
    titleKeyword: "TD19",
    synonyms: [
      "td19", "extra ue", "extra cee", "fuori ue", "paesi terzi", "importazione",
      "beni esteri", "art 17 c2", "art.17 c.2", "acquisto beni estero"
    ],
    intentLabel: "Autofattura acquisto beni da soggetti extra-UE (TD19)"
  },
  {
    id: "TD24",
    titleKeyword: "TD24",
    synonyms: [
      "td24", "differita", "fattura differita", "ddt", "documento di trasporto",
      "riepilogativa", "mensile", "autotrasportatori", "art 21"
    ],
    intentLabel: "Fattura differita su DDT (TD24)"
  },
  {
    id: "TD27",
    titleKeyword: "TD27",
    synonyms: [
      "td27", "autoconsumo", "omaggio", "omaggi", "cessione gratuita",
      "campioni", "uso personale", "uso proprio", "beni gratuiti"
    ],
    intentLabel: "Autoconsumo/cessioni gratuite (TD27)"
  },
  {
    id: "OSS",
    titleKeyword: "OSS",
    synonyms: [
      "oss", "moss", "one stop shop", "ecommerce", "e-commerce",
      "b2c", "privati ue", "consumatori ue", "vendita online", "negozio online",
      "soglia", "10000", "commercio elettronico"
    ],
    intentLabel: "Regime OSS/MOSS – e-commerce UE B2C"
  },
  {
    id: "Triangolazione",
    titleKeyword: "triangolazione",
    synonyms: [
      "triangolazione", "triangolare", "tre soggetti", "promotore",
      "cedente", "acquirente", "intermediario", "intra triangolare"
    ],
    intentLabel: "Triangolazione comunitaria (acquisto/vendita triangolare intra-UE)"
  },
  {
    id: "ReverseChargeSett",
    titleKeyword: "reverse charge",
    synonyms: [
      "elettronico", "cellulari", "telefonia", "tablet", "hardware",
      "pulizie", "facchinaggio", "installazione", "lett a-ter", "lett b",
      "energia", "gas", "energetico", "consorzio", "appalti"
    ],
    intentLabel: "Reverse charge settoriale (elettronica, pulizie, energia)"
  },
  {
    id: "IVACassa",
    titleKeyword: "IVA per cassa",
    synonyms: [
      "iva per cassa", "cassa", "differimento", "art 32 bis",
      "esigibilita differita", "pagamento effettivo", "small business"
    ],
    intentLabel: "Regime IVA per cassa (art. 32-bis DL 83/2012)"
  },
  {
    id: "BonusEdilizi",
    titleKeyword: "bonus edilizi",
    synonyms: [
      "bonus", "edilizi", "superbonus", "ecobonus", "sismabonus",
      "sconto fattura", "cessione credito", "110", "90", "65",
      "lavori casa", "ristrutturazione", "enea", "sal"
    ],
    intentLabel: "Bonus edilizi – sconto in fattura e cessione del credito"
  },
  {
    id: "RitenutaAgenti",
    titleKeyword: "provvigioni",
    synonyms: [
      "agente", "agenti", "provvigione", "provvigioni", "rt02",
      "enasarco", "firr", "fnasarco", "mandato", "agenzia"
    ],
    intentLabel: "Ritenuta su provvigioni agenti (RT02) e contributi ENASARCO"
  }
];

// 3. Levenshtein Distance Function for Fuzzy String Match
export function getLevenshteinDistance(a: string, b: string): number {
  const matrix = Array.from({ length: a.length + 1 }, () => Array(b.length + 1).fill(0));

  for (let i = 0; i <= a.length; i++) matrix[i][0] = i;
  for (let j = 0; j <= b.length; j++) matrix[0][j] = j;

  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      if (a[i - 1] === b[j - 1]) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j] + 1,      // deletion
          matrix[i][j - 1] + 1,      // insertion
          matrix[i - 1][j - 1] + 1   // substitution
        );
      }
    }
  }
  return matrix[a.length][b.length];
}

// Helper to check if two words fuzzy-match (Levenshtein distance <= 2 for words longer than 4 chars)
function fuzzyMatch(word1: string, word2: string): boolean {
  const w1 = word1.toLowerCase();
  const w2 = word2.toLowerCase();
  if (w1 === w2) return true;
  if (w1.includes(w2) || w2.includes(w1)) return true;
  if (w1.length < 4 || w2.length < 4) return false;
  
  // Dynamic threshold based on length
  const maxDistance = w1.length > 7 ? 2 : 1;
  return getLevenshteinDistance(w1, w2) <= maxDistance;
}

// 4. Query Tokenizer & Normalizer
export function tokenizeAndClean(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[.,\/#!$%\^&\*;:{}=\-_`~()?"']/g, " ")
    .split(/\s+/)
    .filter((word) => word.trim().length > 1 && !ITALIAN_STOPWORDS.has(word));
}

// 5. Main Scorer & Intent Classifier
export interface ErpMappingCandidate {
  erpName: string;
  notes: string | null;
}

export interface ProcedureCandidate {
  id: string;
  title: string;
  normativeSummary: string;
  electronicInvoicingFields: unknown;
  officialSources: unknown;
  erpMappings: ErpMappingCandidate[];
}

export interface ScoredProcedure {
  procedure: ProcedureCandidate;
  score: number;
}

export interface NlpSearchResult {
  scoredProcedures: ScoredProcedure[];
  detectedIntent: string;
}

export function searchWithNlp(procedures: ProcedureCandidate[], queryText: string): NlpSearchResult {
  if (!queryText.trim()) {
    // If query is empty, return everything with baseline score 1
    return {
      scoredProcedures: procedures.map((p) => ({ procedure: p, score: 1 })),
      detectedIntent: "Visualizzazione catalogo procedure"
    };
  }

  const queryTokens = tokenizeAndClean(queryText);
  let matchedIntentLabel = "";
  
  // Identify if any dictionary intent maps to this query
  const matchingIntents = INTENT_DICTIONARY.filter(intent => {
    return queryTokens.some(token => 
      fuzzyMatch(token, intent.titleKeyword) || 
      intent.synonyms.some(syn => fuzzyMatch(token, syn))
    );
  });

  if (matchingIntents.length > 0) {
    matchedIntentLabel = `Rilevato intento: ${matchingIntents.map(i => i.intentLabel).join(" | ")}`;
  } else {
    matchedIntentLabel = `Ricerca libera per termini: "${queryText}"`;
  }

  const scoredProcedures = procedures
    .map((procedure) => {
      let score = 0;
      const titleTokens = tokenizeAndClean(procedure.title);
      const summaryTokens = tokenizeAndClean(procedure.normativeSummary);

      // B. Intent Synonyms Match (applied once per procedure, not per token)
      matchingIntents.forEach((intent) => {
        if (titleTokens.some(tToken => fuzzyMatch(tToken, intent.titleKeyword))) {
          score += 10;
        }
      });

      // Check query tokens against different parts
      queryTokens.forEach((qToken) => {
        // A. Title Exact/Fuzzy Match (Highest weight)
        titleTokens.forEach((tToken) => {
          if (qToken === tToken) {
            score += 15;
          } else if (fuzzyMatch(qToken, tToken)) {
            score += 8;
          }
        });

        // C. Summary Exact/Fuzzy Match (Medium weight)
        summaryTokens.forEach((sToken) => {
          if (qToken === sToken) {
            score += 5;
          } else if (fuzzyMatch(qToken, sToken)) {
            score += 2;
          }
        });

        // D. ERP Guide Text Match (Bonus weight)
        if (procedure.erpMappings && Array.isArray(procedure.erpMappings)) {
          procedure.erpMappings.forEach((mapping: ErpMappingCandidate) => {
            if (mapping.erpName.toLowerCase().includes(qToken)) {
              score += 4;
            }
            if (mapping.notes && mapping.notes.toLowerCase().includes(qToken)) {
              score += 2;
            }
          });
        }
      });

      return { procedure, score };
    })
    // Only return matching procedures (score > 0)
    .filter((sp) => sp.score > 0)
    // Sort by score descending
    .sort((a, b) => b.score - a.score);

  return {
    scoredProcedures,
    detectedIntent: matchedIntentLabel
  };
}
