# LexDocs — CLAUDE.md

## Progetto
SaaS per commercialisti e consulenti del lavoro. Ricerca semantica di procedure fiscali italiane con mappatura verso ERP (Zucchetti, TeamSystem, Danea). Prototipo funzionante in fase di test e miglioramento.

## Stack
- **Framework:** Next.js 15 App Router (TypeScript strict)
- **Stile:** Tailwind CSS v4
- **ORM:** Prisma
- **Database:** SQLite locale (`dev.db`) — nessun ambiente staging/produzione al momento
- **Autenticazione:** NON ancora implementata (prossimo obiettivo)

## Struttura
```
src/
  app/
    api/          # Route handlers Next.js
    layout.tsx
    page.tsx
    ProcedureResultCard.tsx
    ShareSnippetButton.tsx
  components/     # Componenti riutilizzabili
  hooks/          # Custom hooks
  lib/            # Utility, client Prisma, helpers
prisma/
  schema.prisma
  seed.ts
  migrations/
  dev.db
```

## Comandi
```bash
npm run dev       # Avvia dev server (localhost:3000)
npm run build     # Build produzione
npx prisma studio # GUI database
npx prisma db push        # Applica schema senza migration
npx prisma migrate dev    # Crea e applica migration
npx prisma db seed        # Popola dati di esempio
```

## Moduli implementati
- `SearchBar.tsx` — input con NLP intent parsing
- `ProcedureResultCard.tsx` — card con tab Normativa / ERP
- `ShareSnippetButton.tsx` — copia/invia snippet WhatsApp o email
- Audit logs ricerche

## Moduli da implementare (priorità ordine)
1. **Autenticazione** — NextAuth.js (utenti, sessioni, ruoli)
2. **Saved procedures** — salvataggio procedure preferite per utente
3. **ERP distribution chart** — analytics query per ERP
4. **PDF export** — esportazione procedure in PDF

## Convenzioni
- TypeScript strict: nessun `any`
- Commenti in italiano su ogni funzione e blocco logico non ovvio
- Indentazione 2 spazi (standard Next.js/Prettier)
- Conventional commits in italiano: `feat:`, `fix:`, `refactor:`, ecc.
- Tailwind: usa classi semantiche, no valori arbitrari se esiste un token
