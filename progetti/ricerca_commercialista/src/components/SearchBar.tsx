"use client";

import React, { useState, useEffect, useRef } from "react";
import { Search, SlidersHorizontal, Cpu, RotateCcw } from "lucide-react";

interface SearchBarProps {
  onSearch: (query: string, erp: string) => void;
  isLoading?: boolean;
}

function useDebounce(value: string, delay: number): string {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

export default function SearchBar({ onSearch, isLoading = false }: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [selectedErp, setSelectedErp] = useState("");
  const isMounted = useRef(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const debouncedQuery = useDebounce(query, 300);

  // Ctrl+K / Cmd+K → focus the search input
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        inputRef.current?.focus();
        inputRef.current?.select();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // Fires search 300ms after the user stops typing; skips the initial mount
  useEffect(() => {
    if (!isMounted.current) {
      isMounted.current = true;
      return;
    }
    onSearch(debouncedQuery, selectedErp);
  }, [debouncedQuery]); // eslint-disable-line react-hooks/exhaustive-deps

  const erpOptions = [
    { value: "", label: "Tutti i Gestionali" },
    { value: "Zucchetti", label: "Zucchetti" },
    { value: "TeamSystem", label: "TeamSystem" },
    { value: "Danea", label: "Danea" },
    { value: "Mexal", label: "Mexal" },
    { value: "Fatture in Cloud", label: "Fatture in Cloud" },
    { value: "Sistemi / Profis", label: "Sistemi / Profis" },
    { value: "Buffetti / Blustring", label: "Buffetti / Blustring" },
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(query, selectedErp);
  };

  const handleReset = () => {
    setQuery("");
    setSelectedErp("");
    onSearch("", "");
  };

  return (
    <form onSubmit={handleSubmit} className="w-full space-y-4">
      {/* Search Input Container */}
      <div className="relative group">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-500 rounded-2xl blur opacity-25 group-hover:opacity-40 transition duration-300"></div>
        <div className="relative flex items-center bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 transition duration-200">
          <div className="pl-5 text-slate-400">
            <Search className="h-6 w-6" />
          </div>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Cerca una procedura fiscale (es. 'Autofattura TD17', 'Reverse charge edilizia'...)"
            className="w-full px-4 py-4 text-slate-100 bg-transparent placeholder-slate-400 outline-none text-base md:text-lg"
          />
          {isLoading ? (
            <div className="pr-5">
              <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-500 border-t-transparent"></div>
            </div>
          ) : query || selectedErp ? (
            <button
              type="button"
              onClick={handleReset}
              className="p-2 mr-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition"
              title="Azzera filtri"
            >
              <RotateCcw className="h-5 w-5" />
            </button>
          ) : (
            <kbd className="hidden sm:flex items-center gap-1 mr-4 px-2 py-1 text-[10px] font-mono font-semibold text-slate-500 bg-slate-800/60 border border-slate-700/60 rounded-md pointer-events-none select-none">
              <span>Ctrl</span>
              <span>K</span>
            </kbd>
          )}
          <button
            type="submit"
            className="px-6 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium hover:from-blue-500 hover:to-indigo-500 transition duration-150 h-full shrink-0 flex items-center gap-2"
          >
            <span>Cerca</span>
          </button>
        </div>
      </div>

      {/* Filter Badges and Selects */}
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <span className="flex items-center gap-1.5 text-slate-400 font-medium">
          <SlidersHorizontal className="h-4 w-4" />
          <span>Filtra per ERP:</span>
        </span>
        <div className="flex flex-wrap gap-2">
          {erpOptions.map((opt) => {
            const isSelected = selectedErp === opt.value;
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => {
                  setSelectedErp(opt.value);
                  onSearch(query, opt.value);
                }}
                className={`px-3 py-1.5 rounded-full border text-xs font-semibold flex items-center gap-1.5 transition duration-150 ${
                  isSelected
                    ? "bg-blue-500/10 border-blue-500 text-blue-400 shadow-sm"
                    : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-300"
                }`}
              >
                <Cpu className="h-3.5 w-3.5" />
                {opt.label}
              </button>
            );
          })}
        </div>
      </div>
    </form>
  );
}
