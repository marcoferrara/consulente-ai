interface OfficialSource {
  source_name: string;
  url: string;
  target_paragraph: string;
}

interface ElectronicInvoicingFields {
  tipo_documento: string;
  natura_iva: string;
  bollo_virtuale?: string;
  importo_bollo?: string;
  descrizione?: string;
}

interface ErpMapping {
  erpName: string;
  stepByStepGuide: string[];
  notes: string | null;
}

interface ProcedureForExport {
  id: string;
  title: string;
  normativeSummary: string;
  electronicInvoicingFields: unknown;
  officialSources: unknown;
  erpMappings: ErpMapping[];
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function exportProcedureToPDF(procedure: ProcedureForExport, selectedErpIndex?: number): void {
  const fe = procedure.electronicInvoicingFields as ElectronicInvoicingFields;
  const sources = (procedure.officialSources as OfficialSource[]) ?? [];
  // Esporta solo l'ERP selezionato se specificato, altrimenti tutti
  const allErps = procedure.erpMappings ?? [];
  const erps = selectedErpIndex !== undefined && allErps[selectedErpIndex]
    ? [allErps[selectedErpIndex]]
    : allErps;
  const erpSectionTitle = erps.length === 1
    ? `Guida Operativa — ${escapeHtml(erps[0].erpName)}`
    : "Guide Operative Gestionali ERP";
  const generatedAt = new Date().toLocaleDateString("it-IT", {
    day: "2-digit", month: "long", year: "numeric",
  });

  const sdiRows = [
    ["Tipo Documento", `<span class="badge">${escapeHtml(fe.tipo_documento)}</span>`],
    ["Natura IVA", fe.natura_iva
      ? `<span class="badge indigo">${escapeHtml(fe.natura_iva)}</span>`
      : `<span class="muted">N/D — Aliquota ordinaria</span>`],
    ...(fe.bollo_virtuale === "SI" ? [
      ["Imposta di Bollo", `<span class="badge amber">Virtuale — €${fe.importo_bollo ?? "2.00"}</span>`],
    ] : []),
    ...(fe.descrizione ? [["Descrizione", escapeHtml(fe.descrizione)]] : []),
  ];

  const sourcesHtml = sources.length === 0
    ? `<p class="muted">Nessuna fonte ufficiale indicata.</p>`
    : sources.map(s => `
        <div class="source-item">
          <div class="source-name">
            <a href="${escapeHtml(s.url)}" target="_blank">${escapeHtml(s.source_name)}</a>
          </div>
          <div class="source-para">↳ ${escapeHtml(s.target_paragraph)}</div>
        </div>`).join("");

  const erpsHtml = erps.length === 0
    ? `<p class="muted">Nessuna guida gestionale disponibile.</p>`
    : erps.map(erp => `
        <div class="erp-block">
          <div class="erp-name">${escapeHtml(erp.erpName)}</div>
          <div class="steps">
            ${erp.stepByStepGuide.map((step, i) => `
              <div class="step">
                <div class="step-num">${i + 1}</div>
                <div class="step-text">${escapeHtml(step)}</div>
              </div>`).join("")}
          </div>
          ${erp.notes ? `<div class="notes"><strong>Note:</strong> ${escapeHtml(erp.notes)}</div>` : ""}
        </div>`).join("");

  const html = `<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LexDocs — ${escapeHtml(procedure.title)}</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', system-ui, Arial, sans-serif;
      font-size: 13px;
      color: #1e293b;
      background: #fff;
      padding: 40px 48px;
      line-height: 1.5;
    }

    /* ── Header ── */
    .doc-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      padding-bottom: 16px;
      margin-bottom: 28px;
      border-bottom: 3px solid #3b82f6;
    }
    .logo-name { font-size: 22px; font-weight: 900; color: #3b82f6; letter-spacing: -0.5px; }
    .logo-sub  { font-size: 9px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.12em; margin-top: 1px; }
    .doc-meta  { font-size: 10px; color: #94a3b8; text-align: right; line-height: 1.6; }

    /* ── Titles ── */
    h1 { font-size: 20px; font-weight: 800; color: #0f172a; margin-bottom: 4px; }
    .proc-id { font-size: 10px; color: #3b82f6; font-family: monospace; margin-bottom: 28px; }

    /* ── Section headings ── */
    h2 {
      font-size: 10px; font-weight: 700; color: #64748b;
      text-transform: uppercase; letter-spacing: 0.1em;
      margin: 28px 0 10px;
      padding-bottom: 5px;
      border-bottom: 1px solid #e2e8f0;
    }

    /* ── Summary ── */
    .summary {
      font-size: 13px; line-height: 1.75; color: #334155;
      background: #f8fafc;
      border-left: 3px solid #3b82f6;
      padding: 12px 16px;
      border-radius: 0 6px 6px 0;
    }

    /* ── SDI table ── */
    .sdi-table { width: 100%; border-collapse: collapse; }
    .sdi-table tr:first-child td { border-top: 1px solid #e2e8f0; }
    .sdi-table td { padding: 9px 12px; border-bottom: 1px solid #e2e8f0; vertical-align: middle; }
    .sdi-table td:first-child { font-weight: 600; color: #475569; background: #f8fafc; width: 38%; font-size: 12px; }
    .badge       { display: inline-block; padding: 2px 9px; border-radius: 4px; font-family: monospace; font-size: 12px; font-weight: 700; background: #eff6ff; color: #3b82f6; border: 1px solid #bfdbfe; }
    .badge.indigo { background: #eef2ff; color: #6366f1; border-color: #c7d2fe; }
    .badge.amber  { background: #fffbeb; color: #d97706; border-color: #fde68a; }
    .muted { color: #94a3b8; font-style: italic; }

    /* ── Sources ── */
    .source-item { padding: 8px 0; border-bottom: 1px solid #f1f5f9; }
    .source-item:last-child { border-bottom: none; }
    .source-name a { color: #3b82f6; text-decoration: none; font-weight: 600; font-size: 12px; }
    .source-para { font-size: 10px; color: #94a3b8; margin-top: 3px; }

    /* ── ERP Guides ── */
    .erp-block { margin-bottom: 22px; padding: 16px; border: 1px solid #e2e8f0; border-radius: 8px; page-break-inside: avoid; }
    .erp-name  { font-size: 13px; font-weight: 700; color: #1d4ed8; margin-bottom: 12px; }
    .step      { display: flex; gap: 10px; margin-bottom: 8px; align-items: flex-start; }
    .step-num  {
      min-width: 22px; height: 22px; border-radius: 50%;
      background: #3b82f6; color: #fff;
      display: flex; align-items: center; justify-content: center;
      font-size: 10px; font-weight: 700; flex-shrink: 0;
    }
    .step-text { color: #334155; line-height: 1.6; font-size: 12px; }
    .notes {
      margin-top: 10px; font-size: 11px; color: #78350f;
      background: #fffbeb; border: 1px solid #fde68a;
      border-radius: 5px; padding: 8px 12px;
    }

    /* ── Footer ── */
    .doc-footer {
      margin-top: 40px; padding-top: 12px;
      border-top: 1px solid #e2e8f0;
      display: flex; justify-content: space-between;
      font-size: 10px; color: #cbd5e1;
    }

    /* ── Print overrides ── */
    @media print {
      body { padding: 0; }
      @page { margin: 18mm 20mm; size: A4; }
      a { color: inherit !important; }
    }
  </style>
</head>
<body>

  <div class="doc-header">
    <div>
      <div class="logo-name">LexDocs</div>
      <div class="logo-sub">Raccordo Fiscale &amp; ERP</div>
    </div>
    <div class="doc-meta">
      Scheda Procedura Fiscale<br>
      Generata il ${escapeHtml(generatedAt)}
    </div>
  </div>

  <h1>${escapeHtml(procedure.title)}</h1>
  <div class="proc-id">ID: ${escapeHtml(procedure.id)}</div>

  <h2>Sintesi Fiscale Normativa</h2>
  <div class="summary">${escapeHtml(procedure.normativeSummary)}</div>

  <h2>Parametri XML SDI — Fatturazione Elettronica</h2>
  <table class="sdi-table">
    ${sdiRows.map(([label, value]) => `<tr><td>${escapeHtml(label as string)}</td><td>${value}</td></tr>`).join("")}
  </table>

  <h2>Fonti e Riferimenti Ufficiali</h2>
  ${sourcesHtml}

  <h2>${erpSectionTitle}</h2>
  ${erpsHtml}

  <div class="doc-footer">
    <span>LexDocs Platform — Sistema di Raccordo Fiscale &amp; ERP per Professionisti</span>
    <span>${escapeHtml(procedure.id)}</span>
  </div>

  <script>
    window.addEventListener('load', () => {
      window.print();
      window.addEventListener('afterprint', () => window.close());
    });
  </script>
</body>
</html>`;

  const printWindow = window.open("", "_blank", "width=900,height=700");
  if (!printWindow) return;
  printWindow.document.write(html);
  printWindow.document.close();
}
