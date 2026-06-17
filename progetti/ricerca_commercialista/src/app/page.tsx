"use client";

import React, { useState, useEffect } from "react";
import {
  Clock,
  History,
  UserCheck,
  TrendingUp,
  X,
  PlusCircle,
  HelpCircle,
  Building,
  Sparkles,
  Plus,
  Bookmark,
  Cpu,
  BarChart3,
  ChevronRight,
  Zap,
} from "lucide-react";
import { useBookmarks } from "@/hooks/useBookmarks";
import SearchBar from "@/components/SearchBar";
import ProcedureResultCard from "@/components/ProcedureResultCard";

interface ElectronicInvoicingFields {
  tipo_documento: string;
  natura_iva: string;
  bollo_virtuale?: string;
  importo_bollo?: string;
  descrizione?: string;
}

interface OfficialSource {
  source_name: string;
  url: string;
  target_paragraph: string;
}

interface ErpMapping {
  id: string;
  procedureId: string;
  erpName: string;
  stepByStepGuide: string[];
  notes: string | null;
}

interface Procedure {
  id: string;
  title: string;
  normativeSummary: string;
  electronicInvoicingFields: ElectronicInvoicingFields;
  officialSources: OfficialSource[];
  erpMappings: ErpMapping[];
}

interface SearchLogUser {
  name: string;
  email: string;
  role: string;
}

interface SearchLog {
  id: string;
  userId: string;
  query: string;
  erpFilter: string | null;
  searchIntent: string | null;
  matchedProceduresCount: number;
  responseGiven: string;
  executionTimeMs: number;
  createdAt: string;
  user: SearchLogUser;
}

interface StudioStats {
  totalSearches: number;
  averageExecutionTimeMs: number;
  erpDistribution: Record<string, number>;
}

interface ErpMappingField {
  erpName: string;
  stepByStepGuide: string[];
  notes: string;
}

// Righe skeleton per il pannello lista durante il caricamento
function SkeletonList() {
  return (
    <div className="space-y-1 p-2 animate-pulse">
      {[...Array(9)].map((_, i) => (
        <div key={i} className="flex items-center gap-3 px-4 py-3.5 rounded-xl">
          <div className="h-6 w-10 rounded bg-slate-800/80 shrink-0" />
          <div className="flex-1 space-y-1.5">
            <div className="h-3 rounded bg-slate-800/80 w-4/5" />
            <div className="h-2.5 rounded bg-slate-800/60 w-1/3" />
          </div>
        </div>
      ))}
    </div>
  );
}

// Riga compatta del risultato nel pannello lista
function ResultRow({
  procedure,
  isSelected,
  isBookmarked,
  onClick,
}: {
  procedure: Procedure;
  isSelected: boolean;
  isBookmarked: boolean;
  onClick: () => void;
}) {
  const fe = procedure.electronicInvoicingFields;
  return (
    <button
      onClick={onClick}
      className={`w-full text-left px-4 py-3.5 rounded-xl flex items-center gap-3 transition-all duration-150 group border ${
        isSelected
          ? "bg-blue-500/10 border-blue-500/25 shadow-sm"
          : "border-transparent hover:bg-slate-900/60 hover:border-slate-800/60"
      }`}
    >
      <span
        className={`text-[10px] font-mono font-black px-2 py-1 rounded-lg shrink-0 border ${
          isSelected
            ? "bg-blue-500/15 border-blue-500/30 text-blue-300"
            : "bg-slate-900 border-slate-800 text-slate-400 group-hover:text-slate-300"
        }`}
      >
        {fe.tipo_documento}
      </span>
      <div className="flex-1 min-w-0">
        <p
          className={`text-xs font-semibold leading-snug line-clamp-2 ${
            isSelected ? "text-blue-200" : "text-slate-300 group-hover:text-slate-100"
          }`}
        >
          {procedure.title}
        </p>
        <p className="text-[10px] text-slate-600 mt-0.5 font-mono">
          {procedure.erpMappings.length} ERP
          {fe.natura_iva && !fe.natura_iva.startsWith("(") && (
            <span className="ml-1.5 text-indigo-600">· {fe.natura_iva}</span>
          )}
        </p>
      </div>
      {isBookmarked && (
        <Bookmark className="h-3 w-3 text-amber-400 shrink-0" fill="currentColor" />
      )}
      <ChevronRight
        className={`h-3.5 w-3.5 shrink-0 transition-opacity ${
          isSelected ? "text-blue-400 opacity-100" : "text-slate-700 opacity-0 group-hover:opacity-100"
        }`}
      />
    </button>
  );
}

// Badge intent rilevato dalla ricerca NLP
function IntentBadge({ intent }: { intent: string }) {
  if (!intent) return null;
  // Estrae i termini dopo "Rilevato intento:" separati da " | "
  const prefix = "Rilevato intento:";
  const raw = intent.startsWith(prefix) ? intent.slice(prefix.length).trim() : intent;
  const terms = raw.split("|").map((t) => t.trim()).filter(Boolean).slice(0, 3);
  if (terms.length === 0) return null;

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="flex items-center gap-1 text-[10px] font-bold text-slate-500 uppercase tracking-wider shrink-0">
        <Zap className="h-3 w-3 text-amber-500" />
        Intento
      </span>
      {terms.map((t, i) => (
        <span
          key={i}
          className="px-2.5 py-1 text-[11px] font-semibold rounded-full bg-amber-500/8 border border-amber-500/20 text-amber-400/90"
        >
          {t}
        </span>
      ))}
    </div>
  );
}

export default function Dashboard() {
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [logs, setLogs] = useState<SearchLog[]>([]);
  const [stats, setStats] = useState<StudioStats>({
    totalSearches: 0,
    averageExecutionTimeMs: 0,
    erpDistribution: {},
  });

  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchErp, setSearchErp] = useState("");
  const [detectedIntent, setDetectedIntent] = useState("");
  const [selectedProcedureId, setSelectedProcedureId] = useState<string | null>(null);
  const [activePanel, setActivePanel] = useState<"bookmarks" | "logs">("logs");
  const { bookmarks, toggleBookmark, isBookmarked } = useBookmarks();

  const [isAdminOpen, setIsAdminOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newSummary, setNewSummary] = useState("");
  const [newDocType, setNewDocType] = useState("TD01");
  const [newNaturaIva, setNewNaturaIva] = useState("");
  const [newBolloVirtuale, setNewBolloVirtuale] = useState(false);
  const [newSources, setNewSources] = useState<OfficialSource[]>([
    { source_name: "", url: "", target_paragraph: "" },
  ]);
  const [newErpMappings, setNewErpMappings] = useState<ErpMappingField[]>([
    { erpName: "Zucchetti Mago/Adhoc", stepByStepGuide: [""], notes: "" },
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [submitSuccess, setSubmitSuccess] = useState("");

  const selectedProcedure =
    procedures.find((p) => p.id === selectedProcedureId) ?? procedures[0] ?? null;

  const fetchSearchResults = async (query = "", erp = "") => {
    setIsLoading(true);
    try {
      const res = await fetch(
        `/api/v1/search?q=${encodeURIComponent(query)}&erp=${encodeURIComponent(erp)}`
      );
      const result = await res.json();
      if (result.success) {
        setProcedures(result.data);
        setDetectedIntent(result.detectedIntent ?? "");
        setSelectedProcedureId(result.data[0]?.id ?? null);
      }
    } catch (err) {
      console.error("Error searching procedures:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchStudioLogs = async () => {
    try {
      const res = await fetch("/api/v1/logs/studio");
      const result = await res.json();
      if (result.success) {
        setLogs(result.data.logs);
        setStats(result.data.stats);
      }
    } catch (err) {
      console.error("Error fetching logs:", err);
    }
  };

  useEffect(() => {
    let active = true;
    const init = async () => {
      try {
        const [searchRes, logsRes] = await Promise.all([
          fetch("/api/v1/search"),
          fetch("/api/v1/logs/studio"),
        ]);
        const searchResult = await searchRes.json();
        const logsResult = await logsRes.json();
        if (active) {
          if (searchResult.success) {
            setProcedures(searchResult.data);
            setDetectedIntent(searchResult.detectedIntent ?? "");
            setSelectedProcedureId(searchResult.data[0]?.id ?? null);
          }
          if (logsResult.success) {
            setLogs(logsResult.data.logs);
            setStats(logsResult.data.stats);
          }
          setIsLoading(false);
        }
      } catch {
        if (active) setIsLoading(false);
      }
    };
    init();
    return () => { active = false; };
  }, []);

  const handleSearch = async (query: string, erp: string) => {
    setSearchQuery(query);
    setSearchErp(erp);
    await fetchSearchResults(query, erp);
    fetchStudioLogs();
  };

  // Form helpers
  const addSourceField = () =>
    setNewSources((p) => [...p, { source_name: "", url: "", target_paragraph: "" }]);
  const removeSourceField = (i: number) =>
    setNewSources((p) => p.filter((_, idx) => idx !== i));
  const addErpMappingField = () =>
    setNewErpMappings((p) => [
      ...p,
      { erpName: "Zucchetti Mago/Adhoc", stepByStepGuide: [""], notes: "" },
    ]);
  const removeErpMappingField = (i: number) =>
    setNewErpMappings((p) => p.filter((_, idx) => idx !== i));
  const handleStepChange = (mapIdx: number, stepIdx: number, val: string) =>
    setNewErpMappings((p) =>
      p.map((m, i) => {
        if (i !== mapIdx) return m;
        const steps = [...m.stepByStepGuide];
        steps[stepIdx] = val;
        return { ...m, stepByStepGuide: steps };
      })
    );
  const addStepField = (mapIdx: number) =>
    setNewErpMappings((p) =>
      p.map((m, i) =>
        i === mapIdx ? { ...m, stepByStepGuide: [...m.stepByStepGuide, ""] } : m
      )
    );
  const removeStepField = (mapIdx: number, stepIdx: number) =>
    setNewErpMappings((p) =>
      p.map((m, i) =>
        i !== mapIdx ? m : { ...m, stepByStepGuide: m.stepByStepGuide.filter((_, j) => j !== stepIdx) }
      )
    );

  const handleCreateProcedure = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitError("");
    setSubmitSuccess("");

    if (!newTitle.trim() || !newSummary.trim()) {
      setSubmitError("Titolo e sintesi normativa sono obbligatori.");
      setIsSubmitting(false);
      return;
    }

    const cleanSources = newSources.filter((s) => s.source_name.trim() && s.url.trim());
    const cleanMappings = newErpMappings
      .map((m) => ({
        erpName: m.erpName,
        stepByStepGuide: m.stepByStepGuide.filter((s) => s.trim() !== ""),
        notes: m.notes.trim() || null,
      }))
      .filter((m) => m.stepByStepGuide.length > 0);

    const payload = {
      title: newTitle,
      normativeSummary: newSummary,
      electronicInvoicingFields: {
        tipo_documento: newDocType,
        natura_iva: newNaturaIva || null,
        bollo_virtuale: newBolloVirtuale ? "SI" : null,
        importo_bollo: newBolloVirtuale ? "2.00" : null,
      },
      officialSources: cleanSources,
      erpMappings: cleanMappings,
    };

    try {
      const res = await fetch("/api/v1/procedures", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (data.success) {
        setSubmitSuccess("Procedura creata con successo!");
        fetchSearchResults(searchQuery, searchErp);
        fetchStudioLogs();
        setNewTitle("");
        setNewSummary("");
        setNewDocType("TD01");
        setNewNaturaIva("");
        setNewBolloVirtuale(false);
        setNewSources([{ source_name: "", url: "", target_paragraph: "" }]);
        setNewErpMappings([{ erpName: "Zucchetti Mago/Adhoc", stepByStepGuide: [""], notes: "" }]);
        setTimeout(() => { setIsAdminOpen(false); setSubmitSuccess(""); }, 1500);
      } else {
        setSubmitError(data.error || "Impossibile salvare la procedura.");
      }
    } catch {
      setSubmitError("Errore di rete o server non raggiungibile.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="h-screen bg-[#090d16] text-slate-100 flex flex-col font-sans selection:bg-blue-600/35 selection:text-blue-200 overflow-hidden">

      {/* Header */}
      <header className="border-b border-slate-900 bg-slate-950/80 shrink-0 z-40 backdrop-blur-md">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20 shrink-0">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-extrabold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent tracking-tight leading-none">
                LexDocs
              </h1>
              <p className="text-[9px] text-slate-500 font-bold tracking-widest uppercase leading-none mt-0.5">
                Raccordo Fiscale & ERP
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-400">
              <Building className="h-3.5 w-3.5 text-blue-500" />
              <span className="font-semibold text-slate-300">Studio Rossi & Bianchi</span>
            </div>
            <button
              onClick={() => setDrawerOpen(true)}
              className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-bold text-slate-200 rounded-xl transition flex items-center gap-1.5 hover:border-slate-700"
            >
              <BarChart3 className="h-3.5 w-3.5 text-indigo-400" />
              <span className="hidden sm:inline">Studio</span>
            </button>
            <button
              onClick={() => setIsAdminOpen(true)}
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-xs font-bold text-white rounded-xl transition flex items-center gap-1.5 shadow-md shadow-blue-500/20"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Nuova Procedura</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main — layout a tre zone verticali: search, intent, split-pane */}
      <div className="flex-1 overflow-hidden flex flex-col max-w-[1600px] mx-auto w-full px-4 sm:px-6 pt-5 pb-3 gap-4">

        {/* Barra di ricerca */}
        <div className="shrink-0">
          <SearchBar onSearch={handleSearch} isLoading={isLoading} />
        </div>

        {/* Riga info: intent + contatore */}
        <div className="shrink-0 flex items-center justify-between gap-4 flex-wrap">
          <IntentBadge intent={detectedIntent} />
          {!isLoading && (
            <span className="text-xs text-slate-600 font-mono shrink-0">
              {procedures.length} procedure
              {searchQuery && (
                <span className="text-slate-700"> · &quot;{searchQuery}&quot;</span>
              )}
            </span>
          )}
        </div>

        {/* Split pane */}
        <div className="flex-1 overflow-hidden flex gap-0 rounded-2xl border border-slate-900 bg-slate-950/20">

          {/* Pannello lista — sinistra */}
          <div className="w-72 lg:w-80 xl:w-88 shrink-0 border-r border-slate-900 flex flex-col overflow-hidden">
            {/* Header lista */}
            <div className="shrink-0 px-4 py-2.5 border-b border-slate-900 bg-slate-950/40">
              <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                {isLoading ? "Caricamento…" : `${procedures.length} Risultati`}
              </p>
            </div>
            {/* Rows scrollabili */}
            <div className="flex-1 overflow-y-auto">
              {isLoading ? (
                <SkeletonList />
              ) : procedures.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full py-12 px-6 text-center space-y-2">
                  <HelpCircle className="h-8 w-8 text-slate-800" />
                  <p className="text-xs text-slate-500 font-semibold">Nessun risultato</p>
                  <p className="text-[11px] text-slate-600 leading-relaxed">
                    Prova a semplificare il termine o rimuovi il filtro ERP.
                  </p>
                </div>
              ) : (
                <div className="p-2 space-y-0.5">
                  {procedures.map((p) => (
                    <ResultRow
                      key={p.id}
                      procedure={p}
                      isSelected={p.id === (selectedProcedure?.id ?? null)}
                      isBookmarked={isBookmarked(p.id)}
                      onClick={() => setSelectedProcedureId(p.id)}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Pannello dettaglio — destra */}
          <div className="flex-1 overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <div className="flex flex-col items-center gap-3 text-slate-600">
                  <div className="animate-spin rounded-full h-7 w-7 border-2 border-blue-500/40 border-t-blue-500" />
                  <p className="text-xs">Ricerca in corso…</p>
                </div>
              </div>
            ) : selectedProcedure ? (
              <div className="p-5">
                <ProcedureResultCard
                  procedure={selectedProcedure}
                  isBookmarked={isBookmarked(selectedProcedure.id)}
                  onToggleBookmark={() =>
                    toggleBookmark({
                      id: selectedProcedure.id,
                      title: selectedProcedure.title,
                      tipoDocumento:
                        selectedProcedure.electronicInvoicingFields.tipo_documento,
                    })
                  }
                />
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center px-8 space-y-3">
                <div className="h-12 w-12 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center">
                  <ChevronRight className="h-6 w-6 text-slate-700" />
                </div>
                <p className="text-sm font-semibold text-slate-400">
                  Seleziona una procedura
                </p>
                <p className="text-xs text-slate-600 max-w-xs leading-relaxed">
                  Cerca nella barra in alto e clicca una riga per visualizzare normativa e guide ERP.
                </p>
              </div>
            )}
          </div>

        </div>
      </div>

      {/* Drawer overlay */}
      {drawerOpen && (
        <div
          className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-40"
          onClick={() => setDrawerOpen(false)}
        />
      )}

      {/* Drawer Pannello Studio */}
      <div
        className={`fixed top-0 right-0 h-full w-[380px] max-w-full bg-[#090d16] border-l border-slate-800 z-50 overflow-y-auto flex flex-col shadow-2xl transition-transform duration-300 ease-in-out ${
          drawerOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="sticky top-0 z-10 flex items-center justify-between px-5 py-4 border-b border-slate-800 bg-slate-950/90 backdrop-blur-md shrink-0">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-indigo-400" />
            <span className="text-sm font-bold text-slate-200">Pannello Studio</span>
          </div>
          <button
            onClick={() => setDrawerOpen(false)}
            className="p-1.5 text-slate-500 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 p-4 space-y-6">
          <div className="grid grid-cols-1 gap-4">
            <div className="bg-slate-900/40 border border-slate-900 rounded-2xl p-4 flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                  Ricerche Totali Studio
                </p>
                <p className="text-2xl font-black text-slate-100">{stats.totalSearches}</p>
              </div>
              <div className="h-10 w-10 rounded-xl bg-blue-500/10 flex items-center justify-center border border-blue-500/20">
                <TrendingUp className="h-5 w-5 text-blue-400" />
              </div>
            </div>

            <div className="bg-slate-900/40 border border-slate-900 rounded-2xl p-4 flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                  Tempo Risposta Medio
                </p>
                <p className="text-2xl font-black text-emerald-400">
                  {stats.averageExecutionTimeMs} ms
                </p>
              </div>
              <div className="h-10 w-10 rounded-xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                <Clock className="h-5 w-5 text-emerald-400" />
              </div>
            </div>
          </div>

          {/* ERP Distribution */}
          {(() => {
            const entries = Object.entries(stats.erpDistribution).sort(([, a], [, b]) => b - a);
            if (entries.length === 0) return null;
            const max = entries[0][1];
            const total = entries.reduce((s, [, n]) => s + n, 0);
            const BAR_COLORS = ["bg-blue-500", "bg-indigo-500", "bg-violet-500", "bg-sky-500", "bg-cyan-500"];
            return (
              <div className="bg-slate-900/40 border border-slate-900 rounded-2xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Cpu className="h-3.5 w-3.5 text-blue-500" />
                    <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                      Distribuzione ERP
                    </p>
                  </div>
                  <span className="text-[10px] text-slate-600 font-mono">{total} ricerche filtrate</span>
                </div>
                <div className="space-y-2.5">
                  {entries.map(([erp, count], idx) => {
                    const pct = max > 0 ? (count / max) * 100 : 0;
                    const sharePct = total > 0 ? Math.round((count / total) * 100) : 0;
                    const color = BAR_COLORS[idx % BAR_COLORS.length];
                    return (
                      <div key={erp}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[11px] text-slate-300 font-semibold truncate max-w-[60%]">
                            {erp}
                          </span>
                          <div className="flex items-center gap-1.5 shrink-0">
                            <span className="text-[10px] text-slate-500 font-mono">{count}</span>
                            <span className="text-[9px] text-slate-700 font-mono">({sharePct}%)</span>
                          </div>
                        </div>
                        <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${color} rounded-full transition-all duration-700`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })()}

          {/* Tabs: Salvate / Audit Logs */}
          <div className="bg-slate-950/60 border border-slate-900 rounded-2xl flex flex-col overflow-hidden min-h-[300px]">
            <div className="flex border-b border-slate-900 bg-slate-950/80 shrink-0">
              <button
                onClick={() => setActivePanel("bookmarks")}
                className={`flex-1 py-3 text-[10px] font-bold uppercase tracking-wider flex items-center justify-center gap-1.5 border-b-2 transition ${
                  activePanel === "bookmarks"
                    ? "border-amber-500 text-amber-400"
                    : "border-transparent text-slate-500 hover:text-slate-300"
                }`}
              >
                <Bookmark className="h-3.5 w-3.5" fill={activePanel === "bookmarks" ? "currentColor" : "none"} />
                Salvate ({bookmarks.length})
              </button>
              <button
                onClick={() => setActivePanel("logs")}
                className={`flex-1 py-3 text-[10px] font-bold uppercase tracking-wider flex items-center justify-center gap-1.5 border-b-2 transition ${
                  activePanel === "logs"
                    ? "border-blue-500 text-blue-400"
                    : "border-transparent text-slate-500 hover:text-slate-300"
                }`}
              >
                <History className="h-3.5 w-3.5" />
                Audit Logs
              </button>
            </div>

            {activePanel === "bookmarks" && (
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {bookmarks.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 text-center space-y-2">
                    <Bookmark className="h-8 w-8 text-slate-700" />
                    <p className="text-xs text-slate-600 italic">Nessuna procedura salvata.</p>
                    <p className="text-[10px] text-slate-700 max-w-[180px] leading-relaxed">
                      Clicca l&apos;icona segnalibro su una procedura per salvarla qui.
                    </p>
                  </div>
                ) : (
                  bookmarks.map((b) => (
                    <div
                      key={b.id}
                      className="flex items-start gap-2 bg-slate-900/40 border border-slate-900/60 p-3 rounded-xl hover:border-amber-500/20 transition group"
                    >
                      <button
                        onClick={() => handleSearch(b.title, "")}
                        className="flex-1 text-left space-y-1 min-w-0"
                      >
                        <span className="inline-block px-1.5 py-0.5 text-[9px] font-mono font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded">
                          {b.tipoDocumento}
                        </span>
                        <p className="text-xs text-slate-200 font-semibold leading-snug line-clamp-2 group-hover:text-amber-300 transition">
                          {b.title}
                        </p>
                      </button>
                      <button
                        onClick={() => toggleBookmark(b)}
                        className="shrink-0 p-1 text-slate-600 hover:text-red-400 transition mt-0.5"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            )}

            {activePanel === "logs" && (
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {logs.length === 0 ? (
                  <p className="text-xs text-slate-600 text-center py-12 italic">
                    Nessuna attività registrata. Le ricerche compariranno qui.
                  </p>
                ) : (
                  logs.map((log) => (
                    <div
                      key={log.id}
                      className="text-xs space-y-1 bg-slate-900/35 border border-slate-900/60 p-3 rounded-xl hover:border-slate-800 transition"
                    >
                      <div className="flex items-center justify-between text-[10px] text-slate-500 font-semibold">
                        <span className="flex items-center gap-1">
                          <UserCheck className="h-3 w-3 text-slate-400" />
                          {log.user.name.split(" ")[0]} ({log.user.role})
                        </span>
                        <span>
                          {new Date(log.createdAt).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                            second: "2-digit",
                          })}
                        </span>
                      </div>
                      <p className="text-slate-300 font-bold leading-tight">
                        Cercato: &quot;{log.query}&quot;
                      </p>
                      <div className="flex items-center justify-between text-[9px] text-slate-500 font-mono mt-2 pt-1.5 border-t border-slate-900/40">
                        <span>ERP: {log.erpFilter || "Tutti"}</span>
                        <span className="text-blue-500 font-semibold">
                          Risultati: {log.matchedProceduresCount} ({log.executionTimeMs}ms)
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal Nuova Procedura */}
      {isAdminOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
          <div className="relative bg-[#0b101d] border border-slate-800 rounded-3xl w-full max-w-3xl shadow-2xl p-6 md:p-8 my-8 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2.5">
                <PlusCircle className="h-6 w-6 text-blue-500" />
                <div>
                  <h3 className="text-lg font-bold text-slate-100">
                    Aggiungi Nuova Procedura Fiscale
                  </h3>
                  <p className="text-xs text-slate-400">
                    Compila la scheda normativa ed associa le guide operative dei gestionali.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsAdminOpen(false)}
                className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-900 rounded-full transition"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreateProcedure} className="py-6 space-y-6">
              {submitError && (
                <div className="bg-red-500/10 border border-red-500/30 text-red-400 p-4 rounded-xl text-sm">
                  {submitError}
                </div>
              )}
              {submitSuccess && (
                <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 p-4 rounded-xl text-sm font-semibold">
                  {submitSuccess}
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Titolo della Procedura
                  </label>
                  <input
                    type="text"
                    required
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="Es. Registrazione Reverse Charge Esterno"
                    className="w-full px-4 py-3 bg-slate-950 border border-slate-800 rounded-xl outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-sm text-slate-100"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Sintesi Fiscale Normativa
                  </label>
                  <textarea
                    required
                    value={newSummary}
                    onChange={(e) => setNewSummary(e.target.value)}
                    rows={3}
                    placeholder="Es. Ai sensi dell'art. 17 comma 2 del DPR 633/72..."
                    className="w-full px-4 py-3 bg-slate-950 border border-slate-800 rounded-xl outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-sm text-slate-100 resize-none"
                  />
                </div>
              </div>

              <div className="p-4 bg-slate-950/40 border border-slate-900 rounded-2xl space-y-4">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Dati di Emissione XML SDI
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1.5">
                      Tipo Documento
                    </label>
                    <select
                      value={newDocType}
                      onChange={(e) => setNewDocType(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl outline-none focus:border-blue-500 text-xs font-mono text-slate-100"
                    >
                      <option value="TD01">TD01 - Fattura ordinaria</option>
                      <option value="TD04">TD04 - Nota di credito</option>
                      <option value="TD16">TD16 - Integrazione reverse charge interno</option>
                      <option value="TD17">TD17 - Integrazione/autofattura servizi esteri</option>
                      <option value="TD18">TD18 - Integrazione beni intracomunitari</option>
                      <option value="TD19">TD19 - Integrazione/autofattura beni ex art. 17 c.2</option>
                      <option value="TD20">TD20 - Autofattura per regolarizzazione</option>
                      <option value="TD24">TD24 - Fattura differita</option>
                      <option value="TD25">TD25 - Fattura differita ex art. 21 c.4 lett. b</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1.5">
                      Natura IVA
                    </label>
                    <input
                      type="text"
                      value={newNaturaIva}
                      onChange={(e) => setNewNaturaIva(e.target.value)}
                      placeholder="Es. N6.3, N2.2"
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl outline-none focus:border-blue-500 text-xs font-mono text-slate-100"
                    />
                  </div>
                  <div className="flex items-center pt-5">
                    <label className="flex items-center gap-2 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={newBolloVirtuale}
                        onChange={(e) => setNewBolloVirtuale(e.target.checked)}
                        className="rounded bg-slate-950 border-slate-800 text-blue-500 focus:ring-0 h-4 w-4"
                      />
                      <span className="text-xs text-slate-400 font-semibold">
                        Applica bollo virtuale (2€)
                      </span>
                    </label>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Fonti ed Riferimenti Ufficiali
                  </label>
                  <button
                    type="button"
                    onClick={addSourceField}
                    className="text-[10px] text-blue-500 font-bold hover:underline"
                  >
                    + Aggiungi Fonte
                  </button>
                </div>
                {newSources.map((source, index) => (
                  <div
                    key={index}
                    className="flex flex-col md:flex-row gap-3 bg-slate-950/20 p-3.5 border border-slate-900 rounded-2xl items-center"
                  >
                    <input
                      type="text"
                      required
                      placeholder="Nome Fonte"
                      value={source.source_name}
                      onChange={(e) => {
                        const val = e.target.value;
                        setNewSources((p) =>
                          p.map((s, i) => (i === index ? { ...s, source_name: val } : s))
                        );
                      }}
                      className="flex-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs outline-none"
                    />
                    <input
                      type="url"
                      required
                      placeholder="URL Documento"
                      value={source.url}
                      onChange={(e) => {
                        const val = e.target.value;
                        setNewSources((p) =>
                          p.map((s, i) => (i === index ? { ...s, url: val } : s))
                        );
                      }}
                      className="flex-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs outline-none"
                    />
                    <input
                      type="text"
                      required
                      placeholder="Paragrafo di riferimento"
                      value={source.target_paragraph}
                      onChange={(e) => {
                        const val = e.target.value;
                        setNewSources((p) =>
                          p.map((s, i) => (i === index ? { ...s, target_paragraph: val } : s))
                        );
                      }}
                      className="w-full md:w-1/4 px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs outline-none"
                    />
                    {newSources.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeSourceField(index)}
                        className="text-slate-500 hover:text-red-400 p-1.5 rounded-full transition"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                ))}
              </div>

              <div className="space-y-4">
                <div className="flex justify-between items-center border-t border-slate-900 pt-4">
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Istruzioni Gestionali ERP
                  </label>
                  <button
                    type="button"
                    onClick={addErpMappingField}
                    className="text-[10px] text-blue-500 font-bold hover:underline"
                  >
                    + Aggiungi Software ERP
                  </button>
                </div>
                {newErpMappings.map((mapping, mapIdx) => (
                  <div
                    key={mapIdx}
                    className="bg-slate-950/20 p-4 border border-slate-900 rounded-2xl space-y-4"
                  >
                    <div className="flex justify-between items-center gap-2">
                      <div className="w-1/2">
                        <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">
                          Software Gestionale
                        </label>
                        <select
                          value={mapping.erpName}
                          onChange={(e) => {
                            const val = e.target.value;
                            setNewErpMappings((p) =>
                              p.map((m, i) => (i === mapIdx ? { ...m, erpName: val } : m))
                            );
                          }}
                          className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl outline-none focus:border-blue-500 text-xs text-slate-100"
                        >
                          <option value="Zucchetti Mago/Adhoc">Zucchetti Mago/Adhoc</option>
                          <option value="TeamSystem">TeamSystem</option>
                          <option value="Danea Easyfatt">Danea Easyfatt</option>
                          <option value="Mexal (Passepartout)">Mexal (Passepartout)</option>
                          <option value="Fatture in Cloud">Fatture in Cloud</option>
                          <option value="Sistemi / Profis">Sistemi Lunare / Profis</option>
                          <option value="Buffetti / Blustring">Buffetti / Blustring</option>
                        </select>
                      </div>
                      {newErpMappings.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeErpMappingField(mapIdx)}
                          className="px-2 py-1 text-[10px] text-red-400 border border-red-500/20 bg-red-500/5 rounded-lg hover:bg-red-500/10 transition"
                        >
                          Rimuovi ERP
                        </button>
                      )}
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <label className="block text-[10px] font-bold text-slate-500 uppercase">
                          Passaggi Operativi
                        </label>
                        <button
                          type="button"
                          onClick={() => addStepField(mapIdx)}
                          className="text-[9px] text-blue-500 hover:underline"
                        >
                          + Aggiungi Passaggio
                        </button>
                      </div>
                      {mapping.stepByStepGuide.map((step, stepIdx) => (
                        <div key={stepIdx} className="flex gap-2 items-center">
                          <span className="text-[10px] font-mono text-slate-600 font-bold shrink-0 w-4">
                            {stepIdx + 1}.
                          </span>
                          <input
                            type="text"
                            required
                            placeholder="Es. Selezionare causale contabile 'FAEU'..."
                            value={step}
                            onChange={(e) => handleStepChange(mapIdx, stepIdx, e.target.value)}
                            className="flex-1 px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs outline-none focus:border-blue-500"
                          />
                          {mapping.stepByStepGuide.length > 1 && (
                            <button
                              type="button"
                              onClick={() => removeStepField(mapIdx, stepIdx)}
                              className="text-slate-600 hover:text-red-400 transition"
                            >
                              <X className="h-3.5 w-3.5" />
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">
                        Note integrative (Opzionale)
                      </label>
                      <input
                        type="text"
                        placeholder="Es. Nel piano dei conti, verificare l'attivazione della causale..."
                        value={mapping.notes}
                        onChange={(e) => {
                          const val = e.target.value;
                          setNewErpMappings((p) =>
                            p.map((m, i) => (i === mapIdx ? { ...m, notes: val } : m))
                          );
                        }}
                        className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs outline-none focus:border-blue-500 text-slate-100"
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex justify-end gap-3 pt-6 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAdminOpen(false)}
                  className="px-5 py-2.5 bg-slate-900 border border-slate-800 text-slate-300 text-xs font-semibold rounded-xl hover:bg-slate-800 transition"
                >
                  Annulla
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold rounded-xl transition shadow-md shadow-blue-500/10 flex items-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <div className="animate-spin rounded-full h-3.5 w-3.5 border-2 border-white border-t-transparent" />
                      <span>Salvataggio…</span>
                    </>
                  ) : (
                    <span>Salva Procedura</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
