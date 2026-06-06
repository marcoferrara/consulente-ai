# Implementation Plan — LexDocs AI Upgrade
## Ricerca con Fonti Referenziate · Anthropic Best Practices

> Basato sull'analisi delle fonti NotebookLM (notebook: "Ricerca con Fonti Referenziate — Claude Code & Anthropic API")
> Data: 2026-06-06

---

## Contesto

L'attuale motore di ricerca di LexDocs è interamente rule-based (Levenshtein + dizionario sinonimi in `nlpEngine.ts`). Le `officialSources` sono link statici nel DB. Claude non è mai coinvolto nel flusso di ricerca né nella generazione delle risposte.

Questo piano descrive 4 upgrade incrementali, ognuno deployabile indipendentemente senza breaking change.

---

## Priorità 1 — Citations API sul contenuto esistente

**Obiettivo:** Ogni `normativeSummary` restituita dall'API deve essere generata da Claude con riferimenti ancorati al testo delle fonti ufficiali, non scritta manualmente nel seed.

### Come funziona
- I documenti in `officialSources` (già presenti nel DB come JSON) vengono passati a Claude come blocchi `document` nel prompt
- La Citations API mappa ogni affermazione al `char_location` esatto nel documento sorgente
- Il testo citato non conta nei token di output → nessun costo aggiuntivo

### Modifiche necessarie

**Nuovo file:** `src/lib/claudeCitations.ts`
```ts
// Chiama Claude con Citations API passando le fonti ufficiali della procedura
// Ritorna normativeSummary con citazioni ancorate
import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic();

export async function generateGroundedSummary(
  procedureTitle: string,
  officialSources: { source_name: string; url: string; content: string }[]
): Promise<{ summary: string; citations: Citation[] }> {
  // Costruisce i blocchi document per la Citations API
  // Chiama client.messages.create con documents + citations: { enabled: true }
  // Estrae e ritorna summary + array di citazioni
}
```

**Modifica:** `src/app/api/v1/search/route.ts`
- Aggiungere parametro `?grounded=true` per attivare la generazione con Citations API
- Fallback al campo statico `normativeSummary` se `grounded=false` (compatibilità backward)

**Modifica:** `src/components/ProcedureResultCard.tsx`
- Rendere le citazioni cliccabili con evidenziazione del testo sorgente
- Badge "AI Grounded" quando la risposta proviene da Citations API

**Modifica DB:** Aggiungere colonna `sourceContent text` a `officialSources` nel JSON per memorizzare il testo indicizzato delle fonti (oggi ci sono solo URL e titoli)

### Dipendenze
```bash
npm install @anthropic-ai/sdk
```

### Env var richieste
```
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Priorità 2 — RAG sul corpus normativo

**Obiettivo:** Sostituire `searchWithNlp` con ricerca semantica vettoriale. Il dizionario sinonimi rimane come boost layer sopra il retrieval.

### Architettura target
```
Query utente
    │
    ▼
Tokenizzazione + embedding (text-embedding-3-small o Voyage AI)
    │
    ▼
Vector search su sqlite-vec (compatibile con Prisma esistente)
    │
    ▼
Top-K chunks recuperati → boost con synonym dictionary esistente
    │
    ▼
Chunks iniettati come blocchi "document" nel prompt Claude
    │
    ▼
Risposta con Citations API
```

### Modifiche necessarie

**Nuovo file:** `src/lib/vectorSearch.ts`
```ts
// Gestisce embedding, indexing e similarity search
// Usa sqlite-vec come estensione SQLite (zero infrastruttura aggiuntiva)
// Interface: embedQuery(text) → vector, searchSimilar(vector, topK) → chunks
```

**Nuovo script:** `scripts/indexProcedures.ts`
- Da eseguire una volta dopo il seed (e ad ogni aggiornamento normativo)
- Chunking di `normativeSummary` + `officialSources.content` in frammenti da ~500 token
- Generazione embedding e salvataggio in tabella `ProcedureEmbedding` (nuova)

**Migrazione Prisma:** Aggiungere modello `ProcedureEmbedding`
```prisma
model ProcedureEmbedding {
  id          String   @id @default(cuid())
  procedureId String
  chunkText   String
  embedding   Bytes    // vettore float32 serializzato
  procedure   AccountingProcedure @relation(fields: [procedureId], references: [id])
}
```

**Modifica:** `src/app/api/v1/search/route.ts`
- Aggiungere parametro `?mode=semantic` (default `keyword` per backward compat)
- In modalità semantic: embedding della query → vector search → boost sinonimi → risposta grounded

### Performance
- Prompt Caching (`cache_control: "ephemeral"`) sui blocchi document ripetuti → riduzione costi ~90%
- sqlite-vec è zero-infrastruttura: funziona sul SQLite già presente

---

## Priorità 3 — Claude Agent SDK per query complesse

**Obiettivo:** Per domande articolate multi-procedura, un agente ReAct consulta più procedure in sequenza e sintetizza la risposta con tutte le fonti citate.

### Quando si attiva
- Query con più di 2 intent rilevati simultaneamente (es. "reverse charge + fornitore UE + beni intracomunitari")
- Domande in forma interrogativa esplicita ("Come registro...", "Qual è la procedura per...")
- Parametro esplicito `?agent=true` nell'API

### Architettura

**Nuovo file:** `src/lib/researchAgent.ts`
```ts
// Agente Claude con tool use per ricerca multi-procedura
// Tools disponibili:
//   - searchProcedures(query: string) → chiama il RAG interno
//   - lookupOfficialSource(url: string) → fetch del testo normativo
// Loop ReAct: ragiona → chiama tool → osserva → risponde con Citations API
```

**Nuovo endpoint:** `src/app/api/v1/agent/route.ts`
- POST con body `{ query: string, erpFilter?: string }`
- Streaming della risposta (Server-Sent Events) per UX progressiva
- Hook `PreToolUse`: valida che i tool call non escano dai domini consentiti
- Hook `PostToolUse`: audit log di ogni tool call con costo stimato

**Nuovo componente:** `src/components/AgentAnswerStream.tsx`
- Mostra la risposta in streaming con citazioni inline
- Visualizza il "ragionamento" dell'agente (steps intermedi opzionali)

### Security
```ts
// allowed_domains: limita le ricerche web a sorgenti normative fidate
const TRUSTED_DOMAINS = [
  "agenziaentrate.gov.it",
  "normattiva.it",
  "mef.gov.it",
  "gazzettaufficiale.it",
  "fiscooggi.it"
];
```

---

## Priorità 4 — Web Search per aggiornamenti normativi

**Obiettivo:** Aggiornamento automatico (o on-demand) delle procedure tramite ricerca web su sorgenti normative ufficiali.

### Due modalità

**A. Job periodico (consigliato)**
- Cron settimanale (es. ogni lunedì) che verifica aggiornamenti per ogni procedura
- Usa `web_search_20260209` con query mirate per tipo documento (es. "TD17 aggiornamento 2026 Agenzia Entrate")
- Se trova contenuto nuovo → aggiorna `officialSources.content` + ri-indicizza embedding

**B. On-demand da UI**
- Pulsante "Verifica aggiornamenti" nel `ProcedureResultCard`
- Chiama `POST /api/v1/procedures/:id/refresh` che lancia la ricerca web per quella procedura
- Mostra badge "Aggiornato il [data]" con diff rispetto alla versione precedente

### Nuovo endpoint
```
POST /api/v1/procedures/:id/refresh
```

**Nuovo file:** `src/lib/normativeUpdater.ts`
```ts
// Usa Claude con web_search tool per cercare aggiornamenti normativi
// allowed_domains: solo sorgenti ufficiali italiane
// Compara con il contenuto esistente → propone diff all'utente
// Se confermato → aggiorna DB + ri-indicizza embedding
```

---

## Ordine di implementazione suggerito

```
Settimana 1-2   → Priorità 1: Citations API
                  · Setup Anthropic SDK
                  · claudeCitations.ts
                  · Arricchimento officialSources con content testuale
                  · UI badge "AI Grounded"

Settimana 3-4   → Priorità 2: RAG + Vector Search
                  · sqlite-vec setup
                  · Schema ProcedureEmbedding
                  · Script di indicizzazione
                  · Modalità ?mode=semantic

Settimana 5-6   → Priorità 3: Agent SDK
                  · researchAgent.ts con tool use
                  · Endpoint /api/v1/agent con streaming SSE
                  · AgentAnswerStream component
                  · SDK Hooks per audit + security

Settimana 7     → Priorità 4: Web Search updates
                  · normativeUpdater.ts
                  · Endpoint /refresh
                  · UI "Verifica aggiornamenti"
```

---

## Note tecniche

- **Modello consigliato:** `claude-sonnet-4-5` per Citations API e Agent; `claude-haiku-3-5` per embedding/classificazione
- **Prompt Caching:** Attivare `cache_control: "ephemeral"` su tutti i blocchi document statici (procedure normative) → risparmio ~90% token su query ripetute
- **Backward compatibility:** Ogni priorità aggiunge funzionalità opzionali via query param. Il motore NLP esistente rimane attivo di default fino a Priorità 2 completata
- **Test:** Aggiungere `src/lib/__tests__/claudeCitations.test.ts` e `vectorSearch.test.ts` prima di deprecare `nlpEngine.ts`
