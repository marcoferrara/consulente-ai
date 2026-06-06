"use client";

import { useState, useEffect } from "react";

export interface BookmarkEntry {
  id: string;
  title: string;
  tipoDocumento: string;
}

const STORAGE_KEY = "lexdocs_bookmarks";

export function useBookmarks() {
  const [bookmarks, setBookmarks] = useState<BookmarkEntry[]>([]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) setBookmarks(JSON.parse(raw));
    } catch { /* localStorage not available */ }
  }, []);

  const toggleBookmark = (entry: BookmarkEntry) => {
    setBookmarks(prev => {
      const next = prev.some(b => b.id === entry.id)
        ? prev.filter(b => b.id !== entry.id)
        : [...prev, entry];
      try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)); } catch { /* ignore */ }
      return next;
    });
  };

  const isBookmarked = (id: string) => bookmarks.some(b => b.id === id);

  return { bookmarks, toggleBookmark, isBookmarked };
}
