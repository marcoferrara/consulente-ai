import Anthropic from "@anthropic-ai/sdk";

export interface Citation {
  documentIndex: number;
  sourceName: string;
  citedText: string;
  startCharIndex: number;
  endCharIndex: number;
}

export interface GroundedSummaryResult {
  summary: string;
  citations: Citation[];
}

/**
 * Genera una sintesi normativa ancorata alle fonti ufficiali tramite Citations API.
 * Usa prompt caching sui blocchi document per ridurre i costi su query ripetute (~90%).
 */
export async function generateGroundedSummary(
  procedureTitle: string,
  officialSources: { source_name: string; url: string; content: string }[]
): Promise<GroundedSummaryResult> {
  // Istanza creata a runtime per garantire che process.env.ANTHROPIC_API_KEY sia già caricata da Next.js
  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

  if (officialSources.length === 0) {
    throw new Error("Nessuna fonte disponibile per generare la sintesi grounded.");
  }

  // Costruisce i blocchi document con Citations API e prompt caching
  const documentBlocks: Anthropic.MessageParam["content"] = officialSources.map((src) => ({
    type: "document" as const,
    source: {
      type: "text" as const,
      media_type: "text/plain" as const,
      data: src.content,
    },
    title: src.source_name,
    citations: { enabled: true },
    cache_control: { type: "ephemeral" as const },
  }));

  const userMessage: Anthropic.MessageParam = {
    role: "user",
    content: [
      ...documentBlocks,
      {
        type: "text",
        text: `Sei un consulente fiscale italiano esperto. Analizza le fonti normative fornite e produci una sintesi chiara e precisa della procedura "${procedureTitle}".

La sintesi deve:
- Essere in italiano semplice ma preciso, comprensibile a un commercialista
- Citare esplicitamente le parti rilevanti dei documenti forniti
- Essere di massimo 3-4 frasi
- Includere i riferimenti normativi specifici (articoli, commi, circolari)

Rispondi solo con la sintesi, senza introduzioni o conclusioni.`,
      },
    ],
  };

  const response = await client.messages.create({
    model: "claude-opus-4-8",
    max_tokens: 1024,
    messages: [userMessage],
  });

  // Estrae il testo e le citazioni dalla risposta
  let summaryText = "";
  const citations: Citation[] = [];

  for (const block of response.content) {
    if (block.type === "text") {
      summaryText += block.text;

      // Processa le citazioni inline nel blocco di testo
      if ("citations" in block && Array.isArray(block.citations)) {
        for (const citation of block.citations) {
          if (citation.type === "char_location") {
            citations.push({
              documentIndex: citation.document_index,
              sourceName: officialSources[citation.document_index]?.source_name ?? "",
              citedText: citation.cited_text,
              startCharIndex: citation.start_char_index,
              endCharIndex: citation.end_char_index,
            });
          }
        }
      }
    }
  }

  return {
    summary: summaryText.trim(),
    citations,
  };
}
