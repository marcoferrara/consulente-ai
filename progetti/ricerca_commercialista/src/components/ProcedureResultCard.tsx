"use client";

import React, { useState } from "react";
import { BookOpen, Cpu, Info, ExternalLink, CornerDownRight, Bookmark, FileDown, Sparkles, Quote } from "lucide-react";
import ShareSnippetButton from "./ShareSnippetButton";
import { exportProcedureToPDF } from "@/lib/exportPDF";

interface OfficialSource {
  source_name: string;
  url: string;
  target_paragraph: string;
}

interface AICitation {
  documentIndex: number;
  sourceName: string;
  citedText: string;
  startCharIndex: number;
  endCharIndex: number;
}

interface GroundedResult {
  summary: string;
  citations: AICitation[];
}

interface ElectronicInvoicingFields {
  tipo_documento: string;
  natura_iva: string;
  bollo_virtuale?: string;
  importo_bollo?: string;
  descrizione?: string;
}

interface ErpMapping {
  id: string;
  procedureId: string;
  erpName: string;
  stepByStepGuide: string[]; // array from json
  notes: string | null;
}

interface ProcedureResultCardProps {
  procedure: {
    id: string;
    title: string;
    normativeSummary: string;
    electronicInvoicingFields: unknown;
    officialSources: unknown;
    erpMappings: ErpMapping[];
  };
  isBookmarked: boolean;
  onToggleBookmark: () => void;
  groundedResult?: GroundedResult;
}

export default function ProcedureResultCard({ procedure, isBookmarked, onToggleBookmark, groundedResult }: ProcedureResultCardProps) {
  const [activeTab, setActiveTab] = useState<"normativa" | "erp">("normativa");
  const [selectedErpIndex, setSelectedErpIndex] = useState(0);
  const [expandedCitation, setExpandedCitation] = useState<number | null>(null);

  const feFields = procedure.electronicInvoicingFields as ElectronicInvoicingFields;
  const sources = procedure.officialSources as OfficialSource[];
  const erpMappings = procedure.erpMappings;

  return (
    <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl overflow-hidden shadow-xl transition-all duration-300 hover:border-slate-700/80 hover:shadow-2xl">
      {/* Header */}
      <div className="p-6 border-b border-slate-850 bg-slate-900/40">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h3 className="text-xl font-bold text-slate-100 group-hover:text-blue-400 transition">
              {procedure.title}
            </h3>
            <p className="text-xs text-blue-500 font-semibold tracking-wider uppercase mt-1">
              Id: {procedure.id.slice(0, 8)}...
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={onToggleBookmark}
              title={isBookmarked ? "Rimuovi dai salvati" : "Salva procedura"}
              className={`p-2 rounded-xl border transition duration-150 ${
                isBookmarked
                  ? "bg-amber-500/10 border-amber-500/40 text-amber-400 hover:bg-amber-500/20"
                  : "bg-slate-900 border-slate-800 text-slate-400 hover:border-amber-500/40 hover:text-amber-400"
              }`}
            >
              <Bookmark
                className="h-4 w-4"
                fill={isBookmarked ? "currentColor" : "none"}
              />
            </button>
            <button
              onClick={() => exportProcedureToPDF(procedure, selectedErpIndex)}
              title="Esporta come PDF (gestionale selezionato)"
              className="px-3 py-2 text-xs font-semibold rounded-xl flex items-center gap-2 border transition duration-150 bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-800 hover:border-slate-700 hover:text-emerald-400"
            >
              <FileDown className="h-4 w-4" />
              <span>Esporta PDF</span>
            </button>
            <ShareSnippetButton
              procedureTitle={procedure.title}
              normativeSummary={procedure.normativeSummary}
              feFields={{
                tipo_documento: feFields.tipo_documento,
                natura_iva: feFields.natura_iva,
                bollo_virtuale: feFields.bollo_virtuale,
                importo_bollo: feFields.importo_bollo,
              }}
              erpGuide={erpMappings[selectedErpIndex] ? {
                erpName: erpMappings[selectedErpIndex].erpName,
                steps: erpMappings[selectedErpIndex].stepByStepGuide,
                notes: erpMappings[selectedErpIndex].notes,
              } : undefined}
            />
          </div>
        </div>
      </div>

      {/* Risposta Rapida — campi SDI sempre visibili */}
      <div className="px-6 py-3 bg-slate-950/70 border-b border-slate-800/60 flex items-center gap-4 flex-wrap">
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider shrink-0">Risposta rapida:</span>
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-slate-500">Tipo doc:</span>
          <span className="px-2.5 py-1 text-sm font-mono font-black bg-blue-500/15 text-blue-300 border border-blue-500/30 rounded-lg leading-none">
            {feFields.tipo_documento}
          </span>
        </div>
        {feFields.natura_iva && !feFields.natura_iva.startsWith("(") && (
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-slate-500">Natura IVA:</span>
            <span className="px-2.5 py-1 text-sm font-mono font-black bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 rounded-lg leading-none">
              {feFields.natura_iva}
            </span>
          </div>
        )}
        {feFields.bollo_virtuale === "SI" && (
          <span className="px-2.5 py-1 text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-lg leading-none">
            Bollo {feFields.importo_bollo}€
          </span>
        )}
      </div>

      {/* Tabs Selector */}
      <div className="flex border-b border-slate-850 bg-slate-950/40">
        <button
          onClick={() => setActiveTab("normativa")}
          className={`flex-1 py-3.5 px-4 font-semibold text-sm flex items-center justify-center gap-2 border-b-2 transition duration-200 ${
            activeTab === "normativa"
              ? "border-blue-500 text-blue-400 bg-slate-900/20"
              : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/10"
          }`}
        >
          <BookOpen className="h-4.5 w-4.5" />
          <span>Normativa & Dati SDI</span>
        </button>
        <button
          onClick={() => setActiveTab("erp")}
          className={`flex-1 py-3.5 px-4 font-semibold text-sm flex items-center justify-center gap-2 border-b-2 transition duration-200 ${
            activeTab === "erp"
              ? "border-blue-500 text-blue-400 bg-slate-900/20"
              : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/10"
          }`}
        >
          <Cpu className="h-4.5 w-4.5" />
          <span>Configurazione Gestionale ({erpMappings.length})</span>
        </button>
      </div>

      {/* Content Container */}
      <div className="p-6 min-h-[280px]">
        {activeTab === "normativa" ? (
          <div className="space-y-6 animate-fadeIn">
            {/* Normative Summary */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Info className="h-4 w-4 text-blue-500" />
                <span>Sintesi Fiscale</span>
                {groundedResult && (
                  <span className="ml-auto flex items-center gap-1 px-2 py-0.5 rounded-full bg-violet-500/15 border border-violet-500/30 text-violet-400 text-[10px] font-semibold tracking-wider">
                    <Sparkles className="h-3 w-3" />
                    AI Grounded
                  </span>
                )}
              </h4>
              <p className="text-slate-300 text-sm leading-relaxed bg-slate-950/30 p-4 rounded-xl border border-slate-850/50">
                {groundedResult ? groundedResult.summary : procedure.normativeSummary}
              </p>

              {/* Citazioni ancorate — visibili solo se grounded */}
              {groundedResult && groundedResult.citations.length > 0 && (
                <div className="space-y-1.5 pt-1">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                    Citazioni ({groundedResult.citations.length})
                  </p>
                  {groundedResult.citations.map((citation, idx) => (
                    <div key={idx} className="border border-slate-800 rounded-xl overflow-hidden">
                      <button
                        onClick={() => setExpandedCitation(expandedCitation === idx ? null : idx)}
                        className="w-full flex items-center justify-between gap-2 px-3 py-2 text-left hover:bg-slate-900/40 transition"
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          <Quote className="h-3 w-3 text-violet-500 shrink-0" />
                          <span className="text-[11px] text-slate-400 truncate">{citation.sourceName}</span>
                        </div>
                        <span className="text-[10px] text-slate-600 shrink-0">
                          {expandedCitation === idx ? "▲" : "▼"}
                        </span>
                      </button>
                      {expandedCitation === idx && (
                        <div className="px-3 pb-3">
                          <blockquote className="text-xs text-slate-400 italic border-l-2 border-violet-500/40 pl-3 leading-relaxed">
                            &ldquo;{citation.citedText}&rdquo;
                          </blockquote>
                          <p className="text-[10px] text-slate-600 mt-1">
                            Caratteri {citation.startCharIndex}–{citation.endCharIndex}
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* SDI Electronic Invoicing Codes */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Parametri XML SDI
                </h4>
                <div className="bg-slate-950/50 border border-slate-800 rounded-xl p-4 space-y-3">
                  <div className="flex justify-between items-center pb-2.5 border-b border-slate-800/60">
                    <span className="text-slate-400 text-xs">Tipo Documento:</span>
                    <span className="px-2.5 py-0.5 text-xs font-mono font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded">
                      {feFields.tipo_documento}
                    </span>
                  </div>
                  <div className="flex justify-between items-center pb-2.5 border-b border-slate-800/60">
                    <span className="text-slate-400 text-xs">Natura IVA:</span>
                    <span className="px-2.5 py-0.5 text-xs font-mono font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded">
                      {feFields.natura_iva || "N/D (Aliquota ordinaria)"}
                    </span>
                  </div>
                  {feFields.bollo_virtuale && (
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400 text-xs">Bollo Virtuale:</span>
                      <span className="text-slate-300 text-xs font-semibold">
                        SI ({feFields.importo_bollo}€)
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Official Sources */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Fonti Ufficiali
                </h4>
                <div className="space-y-2">
                  {sources && sources.map((source, idx) => (
                    <a
                      key={idx}
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block p-3 bg-slate-950/30 border border-slate-850 hover:border-slate-700/60 rounded-xl transition duration-150 group"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="text-slate-200 text-xs font-semibold group-hover:text-blue-400 transition line-clamp-1">
                            {source.source_name}
                          </p>
                          <p className="text-slate-400 text-[10px] mt-1 italic flex items-center gap-1">
                            <CornerDownRight className="h-3 w-3 text-slate-500" />
                            {source.target_paragraph}
                          </p>
                        </div>
                        <ExternalLink className="h-3.5 w-3.5 text-slate-500 shrink-0 group-hover:text-blue-400 transition" />
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-6 animate-fadeIn">
            {erpMappings.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-slate-500">
                <Cpu className="h-10 w-10 text-slate-600 mb-2" />
                <p className="text-sm">Nessuna configurazione gestionale mappata per questa procedura.</p>
              </div>
            ) : (
              <div className="flex flex-col lg:flex-row gap-6">
                {/* Left side: ERP Selector */}
                <div className="lg:w-1/4 flex flex-row lg:flex-col gap-2 overflow-x-auto lg:overflow-visible pb-2 lg:pb-0">
                  {erpMappings.map((mapping, idx) => (
                    <button
                      key={mapping.id}
                      onClick={() => setSelectedErpIndex(idx)}
                      className={`px-4 py-2.5 rounded-xl text-left font-medium text-xs whitespace-nowrap transition duration-150 shrink-0 border ${
                        selectedErpIndex === idx
                          ? "bg-blue-500/10 border-blue-500/30 text-blue-400 font-bold"
                          : "bg-slate-950/20 border-slate-850 text-slate-400 hover:bg-slate-900/40 hover:text-slate-200"
                      }`}
                    >
                      {mapping.erpName}
                    </button>
                  ))}
                </div>

                {/* Right side: Step by step Guide */}
                <div className="lg:w-3/4 bg-slate-950/30 border border-slate-850 rounded-2xl p-5 space-y-4">
                  <div>
                    <h4 className="text-sm font-bold text-slate-200">
                      Guida per {erpMappings[selectedErpIndex].erpName}
                    </h4>
                    <p className="text-[10px] text-slate-500 mt-0.5">
                      Segui passo-passo le istruzioni all&apos;interno del software gestionale.
                    </p>
                  </div>

                  {/* Steps */}
                  <div className="space-y-3.5">
                    {erpMappings[selectedErpIndex].stepByStepGuide.map((step, idx) => (
                      <div key={idx} className="flex gap-3 text-sm">
                        <div className="h-5 w-5 rounded-full bg-slate-800 border border-slate-700 text-[10px] font-bold text-slate-400 flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
                          {idx + 1}
                        </div>
                        <p className="text-slate-300 leading-relaxed">{step}</p>
                      </div>
                    ))}
                  </div>

                  {/* Notes */}
                  {erpMappings[selectedErpIndex].notes && (
                    <div className="pt-4 border-t border-slate-850/80">
                      <div className="bg-slate-900/35 border border-slate-800/80 rounded-xl p-3.5 text-xs text-slate-400">
                        <span className="font-bold text-slate-300 block mb-1">Note Importanti:</span>
                        {erpMappings[selectedErpIndex].notes}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
