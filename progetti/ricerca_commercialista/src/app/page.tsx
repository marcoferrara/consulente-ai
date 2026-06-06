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
  const [activePanel, setActivePanel] = useState<"bookmarks" | "logs">("logs");
  const { bookmarks, toggleBookmark, isBookmarked } = useBookmarks();

  // Admin New Procedure Modal State
  const [isAdminOpen, setIsAdminOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newSummary, setNewSummary] = useState("");
  const [newDocType, setNewDocType] = useState("TD01");
  const [newNaturaIva, setNewNaturaIva] = useState("");
  const [newBolloVirtuale, setNewBolloVirtuale] = useState(false);
  const [newSources, setNewSources] = useState<OfficialSource[]>([
    { source_name: "", url: "", target_paragraph: "" }
  ]);
  const [newErpMappings, setNewErpMappings] = useState<ErpMappingField[]>([
    { erpName: "Zucchetti Mago/Adhoc", stepByStepGuide: [""], notes: "" }
  ]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [submitSuccess, setSubmitSuccess] = useState("");

  const fetchSearchResults = async (query = "", erp = "") => {
    setIsLoading(true);
    try {
      const res = await fetch(`/api/v1/search?q=${encodeURIComponent(query)}&erp=${encodeURIComponent(erp)}`);
      const result = await res.json();
      if (result.success) {
        setProcedures(result.data);
      }
    } catch (err) {
      console.error("Error searching procedures:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // 2. Fetch studio audit logs and statistics
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

  // React 19 cleanup-safe initial mount loads, avoiding synchronous state updates in effect
  useEffect(() => {
    let active = true;
    const initializeData = async () => {
      try {
        const [searchRes, logsRes] = await Promise.all([
          fetch("/api/v1/search"),
          fetch("/api/v1/logs/studio")
        ]);
        const searchResult = await searchRes.json();
        const logsResult = await logsRes.json();
        
        if (active) {
          if (searchResult.success) {
            setProcedures(searchResult.data);
          }
          if (logsResult.success) {
            setLogs(logsResult.data.logs);
            setStats(logsResult.data.stats);
          }
          setIsLoading(false);
        }
      } catch (err) {
        console.error(err);
        if (active) setIsLoading(false);
      }
    };
    initializeData();

    return () => {
      active = false;
    };
  }, []);

  const handleSearch = async (query: string, erp: string) => {
    setSearchQuery(query);
    setSearchErp(erp);
    await fetchSearchResults(query, erp);
    fetchStudioLogs();
  };

  // Form helpers
  const addSourceField = () => {
    setNewSources(prev => [...prev, { source_name: "", url: "", target_paragraph: "" }]);
  };

  const removeSourceField = (index: number) => {
    setNewSources(prev => prev.filter((_, i) => i !== index));
  };

  const addErpMappingField = () => {
    setNewErpMappings(prev => [...prev, { erpName: "Zucchetti Mago/Adhoc", stepByStepGuide: [""], notes: "" }]);
  };

  const removeErpMappingField = (index: number) => {
    setNewErpMappings(prev => prev.filter((_, i) => i !== index));
  };

  const handleStepChange = (mapIndex: number, stepIndex: number, val: string) => {
    setNewErpMappings(prev => prev.map((m, i) => {
      if (i !== mapIndex) return m;
      const steps = [...m.stepByStepGuide];
      steps[stepIndex] = val;
      return { ...m, stepByStepGuide: steps };
    }));
  };

  const addStepField = (mapIndex: number) => {
    setNewErpMappings(prev => prev.map((m, i) =>
      i === mapIndex ? { ...m, stepByStepGuide: [...m.stepByStepGuide, ""] } : m
    ));
  };

  const removeStepField = (mapIndex: number, stepIndex: number) => {
    setNewErpMappings(prev => prev.map((m, i) =>
      i !== mapIndex ? m : { ...m, stepByStepGuide: m.stepByStepGuide.filter((_, j) => j !== stepIndex) }
    ));
  };

  // Admin submit handler
  const handleCreateProcedure = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitError("");
    setSubmitSuccess("");

    // Validate inputs
    if (!newTitle.trim() || !newSummary.trim()) {
      setSubmitError("Titolo e sintesi normativa sono obbligatori.");
      setIsSubmitting(false);
      return;
    }

    // Clean data
    const cleanSources = newSources.filter(s => s.source_name.trim() && s.url.trim());
    const cleanMappings = newErpMappings.map(m => ({
      erpName: m.erpName,
      stepByStepGuide: m.stepByStepGuide.filter((step: string) => step.trim() !== ""),
      notes: m.notes.trim() || null
    })).filter(m => m.stepByStepGuide.length > 0);

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
        // Refresh procedures view
        fetchSearchResults(searchQuery, searchErp);
        fetchStudioLogs();

        // Reset Form
        setNewTitle("");
        setNewSummary("");
        setNewDocType("TD01");
        setNewNaturaIva("");
        setNewBolloVirtuale(false);
        setNewSources([{ source_name: "", url: "", target_paragraph: "" }]);
        setNewErpMappings([{ erpName: "Zucchetti Mago/Adhoc", stepByStepGuide: [""], notes: "" }]);

        setTimeout(() => {
          setIsAdminOpen(false);
          setSubmitSuccess("");
        }, 1500);
      } else {
        setSubmitError(data.error || "Impossibile salvare la procedura.");
      }
    } catch (err) {
      console.error(err);
      setSubmitError("Errore di rete o server non raggiungibile.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-sans selection:bg-blue-600/35 selection:text-blue-200">
      {/* Background Glows */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl -z-10"></div>
      <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-indigo-600/5 rounded-full blur-3xl -z-10"></div>

      {/* Top Header Navigation */}
      <header className="border-b border-slate-900 bg-slate-950/80 sticky top-0 z-40 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <Sparkles className="h-5 w-5 text-white animate-pulse" />
            </div>
            <div>
              <h1 className="text-lg font-extrabold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent tracking-tight">
                LexDocs
              </h1>
              <p className="text-[10px] text-slate-500 font-semibold tracking-wider uppercase -mt-0.5">
                Raccordo Fiscale & ERP
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-400">
              <Building className="h-3.5 w-3.5 text-blue-500" />
              <span className="font-semibold text-slate-300">Studio Rossi & Bianchi</span>
            </div>
            <button
              onClick={() => setDrawerOpen(true)}
              className="px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-bold text-slate-200 rounded-xl transition duration-150 flex items-center gap-2 hover:border-slate-700 shadow-md"
            >
              <BarChart3 className="h-4 w-4 text-indigo-400" />
              <span className="hidden sm:inline">Pannello Studio</span>
            </button>
            <button
              onClick={() => setIsAdminOpen(true)}
              className="px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-bold text-slate-200 rounded-xl transition duration-150 flex items-center gap-2 hover:border-slate-700 shadow-md"
            >
              <Plus className="h-4 w-4 text-blue-500" />
              <span>Nuova Procedura</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Body */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">

        {/* Search Panel & Results — full width */}
        <section className="space-y-8">
          {/* Hero Header */}
          <div className="space-y-2">
            <h2 className="text-3xl font-extrabold text-slate-100 tracking-tight">
              Raccordo Normativo e Gestionale
            </h2>
            <p className="text-slate-400 text-sm max-w-2xl leading-relaxed">
              Trova le risposte pratiche ai dubbi di contabilità. Collega i codici SDI della fatturazione elettronica alle guide passo-passo dei principali ERP italiani.
            </p>
          </div>

          {/* Centralized Search Bar */}
          <SearchBar onSearch={handleSearch} isLoading={isLoading} />

          {/* Results Block */}
          <div className="space-y-6">
            <div className="flex justify-between items-center border-b border-slate-900 pb-3">
              <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">
                Risultati della Ricerca ({procedures.length})
              </h3>
              {searchQuery && (
                <span className="text-xs text-slate-500 italic">
                  Filtrato per &quot;{searchQuery}&quot;
                </span>
              )}
            </div>

            {isLoading ? (
              <div className="flex flex-col items-center justify-center py-24 space-y-4">
                <div className="animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent"></div>
                <p className="text-sm text-slate-500">Ricerca nel database fiscale in corso...</p>
              </div>
            ) : procedures.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 bg-slate-900/10 border border-slate-900 rounded-2xl text-center p-6 space-y-3">
                <HelpCircle className="h-10 w-10 text-slate-700" />
                <h4 className="text-slate-300 font-bold">Nessun risultato trovato</h4>
                <p className="text-slate-500 text-sm max-w-sm leading-relaxed">
                  Prova a semplificare il termine cercato o rimuovi il filtro gestionale per visualizzare tutti i riferimenti.
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {procedures.map((procedure) => (
                  <ProcedureResultCard
                    key={procedure.id}
                    procedure={procedure}
                    isBookmarked={isBookmarked(procedure.id)}
                    onToggleBookmark={() => toggleBookmark({
                      id: procedure.id,
                      title: procedure.title,
                      tipoDocumento: procedure.electronicInvoicingFields.tipo_documento,
                    })}
                  />
                ))}
              </div>
            )}
          </div>
        </section>

      </main>

      {/* FOOTER */}
      <footer className="border-t border-slate-950 bg-slate-950/85 py-6">
        <div className="max-w-7xl mx-auto px-4 text-center text-xs text-slate-600">
          <p>© {new Date().getFullYear()} LexDocs Platform - Sistema di Raccordo Fiscale & ERP per Professionisti. Tutti i diritti riservati.</p>
        </div>
      </footer>

      {/* DRAWER OVERLAY */}
      {drawerOpen && (
        <div
          className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-40"
          onClick={() => setDrawerOpen(false)}
        />
      )}

      {/* DRAWER PANNELLO STUDIO */}
      <div
        className={`fixed top-0 right-0 h-full w-[380px] max-w-full bg-[#090d16] border-l border-slate-800 z-50 overflow-y-auto flex flex-col shadow-2xl transition-transform duration-300 ease-in-out ${
          drawerOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Drawer header */}
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
          {/* Drawer Right Side: Studio Administration & Audit Logs (moved from aside) */}
          <aside className="space-y-6 flex flex-col">
          {/* Quick Metrics Cards */}
          <div className="grid grid-cols-1 gap-4">
            {/* Total Queries */}
            <div className="bg-slate-900/40 border border-slate-900 rounded-2xl p-4.5 flex items-center justify-between shadow-md">
              <div className="space-y-1">
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Ricerche Totali Studio</p>
                <p className="text-2xl font-black text-slate-100">{stats.totalSearches}</p>
              </div>
              <div className="h-10 w-10 rounded-xl bg-blue-500/10 flex items-center justify-center border border-blue-500/20">
                <TrendingUp className="h-5 w-5 text-blue-400" />
              </div>
            </div>

            {/* Performance Target Response Time */}
            <div className="bg-slate-900/40 border border-slate-900 rounded-2xl p-4.5 flex items-center justify-between shadow-md">
              <div className="space-y-1">
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Tempo Risposta Medio</p>
                <p className="text-2xl font-black text-emerald-400">{stats.averageExecutionTimeMs} ms</p>
              </div>
              <div className="h-10 w-10 rounded-xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                <Clock className="h-5 w-5 text-emerald-400" />
              </div>
            </div>
          </div>

          {/* ERP Distribution Chart */}
          {(() => {
            const entries = Object.entries(stats.erpDistribution).sort(([, a], [, b]) => b - a);
            if (entries.length === 0) return null;
            const max = entries[0][1];
            const total = entries.reduce((s, [, n]) => s + n, 0);
            const BAR_COLORS = [
              "bg-blue-500",
              "bg-indigo-500",
              "bg-violet-500",
              "bg-sky-500",
              "bg-cyan-500",
            ];
            return (
              <div className="bg-slate-900/40 border border-slate-900 rounded-2xl p-4 shadow-md space-y-3">
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

          {/* Tabbed Panel: Saved Procedures / Audit Logs */}
          <div className="bg-slate-950/60 border border-slate-900 rounded-2xl flex-1 flex flex-col overflow-hidden shadow-lg min-h-[300px]">

            {/* Tab Headers */}
            <div className="flex border-b border-slate-900 bg-slate-950/80 shrink-0">
              <button
                onClick={() => setActivePanel("bookmarks")}
                className={`flex-1 py-3 text-[10px] font-bold uppercase tracking-wider flex items-center justify-center gap-1.5 border-b-2 transition duration-150 ${
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
                className={`flex-1 py-3 text-[10px] font-bold uppercase tracking-wider flex items-center justify-center gap-1.5 border-b-2 transition duration-150 ${
                  activePanel === "logs"
                    ? "border-blue-500 text-blue-400"
                    : "border-transparent text-slate-500 hover:text-slate-300"
                }`}
              >
                <History className="h-3.5 w-3.5" />
                Audit Logs
              </button>
            </div>

            {/* Saved Procedures Panel */}
            {activePanel === "bookmarks" && (
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {bookmarks.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 text-center space-y-2">
                    <Bookmark className="h-8 w-8 text-slate-700" />
                    <p className="text-xs text-slate-600 italic">
                      Nessuna procedura salvata.
                    </p>
                    <p className="text-[10px] text-slate-700 max-w-[180px] leading-relaxed">
                      Clicca l&apos;icona segnalibro su una procedura per salvarla qui.
                    </p>
                  </div>
                ) : (
                  bookmarks.map((b) => (
                    <div
                      key={b.id}
                      className="flex items-start gap-2 bg-slate-900/40 border border-slate-900/60 p-3 rounded-xl hover:border-amber-500/20 transition duration-150 group"
                    >
                      <button
                        onClick={() => handleSearch(b.title, "")}
                        className="flex-1 text-left space-y-1 min-w-0"
                      >
                        <span className="inline-block px-1.5 py-0.5 text-[9px] font-mono font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded">
                          {b.tipoDocumento}
                        </span>
                        <p className="text-xs text-slate-200 font-semibold leading-snug line-clamp-2 group-hover:text-amber-300 transition duration-150">
                          {b.title}
                        </p>
                      </button>
                      <button
                        onClick={() => toggleBookmark(b)}
                        title="Rimuovi dai salvati"
                        className="shrink-0 p-1 text-slate-600 hover:text-red-400 transition duration-150 mt-0.5"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* Audit Logs Panel */}
            {activePanel === "logs" && (
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {logs.length === 0 ? (
                  <p className="text-xs text-slate-600 text-center py-12 italic">
                    Nessuna attività registrata. Le ricerche compariranno qui.
                  </p>
                ) : (
                  logs.map((log) => (
                    <div key={log.id} className="text-xs space-y-1 bg-slate-900/35 border border-slate-900/60 p-3 rounded-xl hover:border-slate-800 transition duration-150">
                      <div className="flex items-center justify-between text-[10px] text-slate-500 font-semibold">
                        <span className="flex items-center gap-1">
                          <UserCheck className="h-3 w-3 text-slate-400" />
                          {log.user.name.split(" ")[0]} ({log.user.role})
                        </span>
                        <span>
                          {new Date(log.createdAt).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                            second: "2-digit"
                          })}
                        </span>
                      </div>
                      <p className="text-slate-300 font-bold leading-tight">
                        Cercato: &quot;{log.query}&quot;
                      </p>
                      <div className="flex items-center justify-between text-[9px] text-slate-500 font-mono mt-2 pt-1.5 border-t border-slate-900/40">
                        <span>ERP: {log.erpFilter || "Tutti"}</span>
                        <span className="text-blue-500 font-semibold">Risultati: {log.matchedProceduresCount} ({log.executionTimeMs}ms)</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </aside>
        </div>
      </div>

      {/* ADMIN ADD PROCEDURE MODAL */}
      {isAdminOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
          <div className="relative bg-[#0b101d] border border-slate-800 rounded-3xl w-full max-w-3xl shadow-2xl p-6 md:p-8 my-8 max-h-[90vh] overflow-y-auto animate-scaleUp">
            
            {/* Modal Header */}
            <div className="flex justify-between items-center pb-4 border-b border-slate-850">
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

            {/* Modal Form */}
            <form onSubmit={handleCreateProcedure} className="py-6 space-y-6">
              
              {/* Form Messages */}
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

              {/* Title & Summary */}
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
                    Sintesi Fiscale Normativa (Max 3 righe)
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

              {/* Invoicing Fields (TD, Natura, Bollo) */}
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
                      <option value="TD17">TD17 - Integrazione/autofattura acquisto servizi esteri</option>
                      <option value="TD18">TD18 - Integrazione acquisto beni intracomunitari</option>
                      <option value="TD19">TD19 - Integrazione/autofattura acquisto beni ex art. 17 c.2</option>
                      <option value="TD20">TD20 - Autofattura per regolarizzazione</option>
                      <option value="TD24">TD24 - Fattura differita</option>
                      <option value="TD25">TD25 - Fattura differita ex art. 21 c.4 lett. b</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1.5">
                      Natura IVA (Se applicabile)
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
                        className="rounded bg-slate-950 border-slate-800 text-blue-500 focus:ring-0 focus:ring-offset-0 h-4 w-4"
                      />
                      <span className="text-xs text-slate-400 font-semibold">Applica bollo virtuale (2€)</span>
                    </label>
                  </div>
                </div>
              </div>

              {/* Official Sources */}
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
                  <div key={index} className="flex flex-col md:flex-row gap-3 bg-slate-950/20 p-3.5 border border-slate-900 rounded-2xl items-center">
                    <input
                      type="text"
                      required
                      placeholder="Nome Fonte (es. Circolare 14/E del 2015)"
                      value={source.source_name}
                      onChange={(e) => {
                        const val = e.target.value;
                        setNewSources(prev => prev.map((s, i) => i === index ? { ...s, source_name: val } : s));
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
                        setNewSources(prev => prev.map((s, i) => i === index ? { ...s, url: val } : s));
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
                        setNewSources(prev => prev.map((s, i) => i === index ? { ...s, target_paragraph: val } : s));
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

              {/* ERP Mapping and Guides */}
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
                  <div key={mapIdx} className="bg-slate-950/20 p-4 border border-slate-900 rounded-2xl space-y-4">
                    <div className="flex justify-between items-center gap-2">
                      <div className="w-1/2">
                        <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">
                          Software Gestionale
                        </label>
                        <select
                          value={mapping.erpName}
                          onChange={(e) => {
                            const val = e.target.value;
                            setNewErpMappings(prev => prev.map((m, i) => i === mapIdx ? { ...m, erpName: val } : m));
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

                    {/* Step by step guide inputs */}
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

                      {mapping.stepByStepGuide.map((step: string, stepIdx: number) => (
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

                    {/* ERP specific notes */}
                    <div>
                      <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">
                        Note integrative del gestionale (Opzionale)
                      </label>
                      <input
                        type="text"
                        placeholder="Es. Nel piano dei conti, verificare l'attivazione della causale..."
                        value={mapping.notes}
                        onChange={(e) => {
                          const val = e.target.value;
                          setNewErpMappings(prev => prev.map((m, i) => i === mapIdx ? { ...m, notes: val } : m));
                        }}
                        className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs outline-none focus:border-blue-500 text-slate-100"
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Submit Buttons */}
              <div className="flex justify-end gap-3 pt-6 border-t border-slate-850">
                <button
                  type="button"
                  onClick={() => setIsAdminOpen(false)}
                  className="px-5 py-2.5 bg-slate-900 border border-slate-800 text-slate-300 text-xs font-semibold rounded-xl hover:bg-slate-800 transition duration-150"
                >
                  Annulla
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold rounded-xl transition duration-150 shadow-md shadow-blue-500/10 flex items-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <div className="animate-spin rounded-full h-3.5 w-3.5 border-2 border-white border-t-transparent"></div>
                      <span>Salvataggio...</span>
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
