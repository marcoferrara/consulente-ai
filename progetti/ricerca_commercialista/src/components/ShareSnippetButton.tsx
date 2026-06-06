"use client";

import React, { useState } from "react";
import { Mail, MessageSquare, Check } from "lucide-react";

interface ErpGuide {
  erpName: string;
  steps: string[];
  notes: string | null;
}

interface ShareSnippetButtonProps {
  procedureTitle: string;
  normativeSummary: string;
  feFields: {
    tipo_documento: string;
    natura_iva: string;
    bollo_virtuale?: string;
    importo_bollo?: string;
  };
  erpGuide?: ErpGuide;
}

export default function ShareSnippetButton({
  procedureTitle,
  normativeSummary,
  feFields,
  erpGuide,
}: ShareSnippetButtonProps) {
  const [copiedType, setCopiedType] = useState<"whatsapp" | "email" | null>(null);

  const getFormattedMessage = (format: "whatsapp" | "email") => {
    const isWa = format === "whatsapp";
    const header = isWa
      ? `*Studio Tributario - Informativa Tecnica*`
      : `Studio Tributario - Informativa Tecnica: ${procedureTitle}`;

    const greeting = "Gentile Cliente,\ncon la presente Le forniamo i riferimenti fiscali e operativi relativi alla procedura in oggetto.";

    const sdiBlock = isWa
      ? `*Dati per la Fatturazione Elettronica:*\n• Tipo Documento: *${feFields.tipo_documento}*\n• Natura IVA: *${feFields.natura_iva}*${
          feFields.bollo_virtuale === "SI" ? `\n• Imposta di Bollo: *Virtuale da 2,00€ (su importi > 77,47€)*` : ""
        }`
      : `Dati per la Fatturazione Elettronica:\n- Tipo Documento: ${feFields.tipo_documento}\n- Natura IVA: ${feFields.natura_iva}${
          feFields.bollo_virtuale === "SI" ? `\n- Imposta di Bollo: Virtuale da 2,00€ (su importi > 77,47€)` : ""
        }`;

    // Guida passaggi nel gestionale selezionato
    const erpBlock = erpGuide && erpGuide.steps.length > 0
      ? isWa
        ? `\n\n*Guida operativa ${erpGuide.erpName}:*\n${erpGuide.steps.map((s, i) => `${i + 1}. ${s}`).join("\n")}${
            erpGuide.notes ? `\n\n⚠️ *Nota:* ${erpGuide.notes}` : ""
          }`
        : `\n\nGuida operativa ${erpGuide.erpName}:\n${erpGuide.steps.map((s, i) => `${i + 1}. ${s}`).join("\n")}${
            erpGuide.notes ? `\n\nNota importante: ${erpGuide.notes}` : ""
          }`
      : "";

    const body = isWa
      ? `\n*Procedura:* _${procedureTitle}_\n\n*Sintesi Normativa:*\n${normativeSummary}\n\n${sdiBlock}${erpBlock}`
      : `Procedura: ${procedureTitle}\n\nSintesi Normativa:\n${normativeSummary}\n\n${sdiBlock}${erpBlock}`;

    const footer = isWa
      ? `\n\nRestiamo a disposizione per qualsiasi chiarimento.\nCordiali saluti.`
      : `\n\nRestiamo a completa disposizione per ulteriori chiarimenti.\n\nCordiali saluti,\nStudio Tributario Rossi & Bianchi`;

    return `${header}\n\n${greeting}\n${body}${footer}`;
  };

  const handleCopy = async (type: "whatsapp" | "email") => {
    const text = getFormattedMessage(type);
    try {
      await navigator.clipboard.writeText(text);
      setCopiedType(type);
      setTimeout(() => setCopiedType(null), 2500);
    } catch (err) {
      console.error("Failed to copy text: ", err);
    }
  };

  return (
    <div className="flex items-center gap-2">
      {/* WhatsApp Formatting Copy */}
      <button
        onClick={() => handleCopy("whatsapp")}
        className={`px-3 py-2 text-xs font-semibold rounded-xl flex items-center gap-2 border transition duration-150 ${
          copiedType === "whatsapp"
            ? "bg-emerald-500/10 border-emerald-500 text-emerald-400"
            : "bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-800 hover:border-slate-700 hover:text-emerald-400"
        }`}
        title="Copia testo formattato per WhatsApp"
      >
        {copiedType === "whatsapp" ? (
          <>
            <Check className="h-4 w-4 text-emerald-400" />
            <span>Copiato per WA!</span>
          </>
        ) : (
          <>
            <MessageSquare className="h-4 w-4" />
            <span>Copia per WhatsApp</span>
          </>
        )}
      </button>

      {/* Email Formatting Copy */}
      <button
        onClick={() => handleCopy("email")}
        className={`px-3 py-2 text-xs font-semibold rounded-xl flex items-center gap-2 border transition duration-150 ${
          copiedType === "email"
            ? "bg-indigo-500/10 border-indigo-500 text-indigo-400"
            : "bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-800 hover:border-slate-700 hover:text-indigo-400"
        }`}
        title="Copia testo formattato per E-mail"
      >
        {copiedType === "email" ? (
          <>
            <Check className="h-4 w-4 text-indigo-400" />
            <span>Copiato per E-mail!</span>
          </>
        ) : (
          <>
            <Mail className="h-4 w-4" />
            <span>Copia per E-mail</span>
          </>
        )}
      </button>
    </div>
  );
}
