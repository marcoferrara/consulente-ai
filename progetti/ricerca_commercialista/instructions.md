# SYSTEM PROMPT / PROJECT SPECIFICATION: "LexDocs" (Working Title)
Role: Senior Full-Stack Software Architect & Lead Developer.
Task: Initialize, architect, and generate the MVP codebase for a high-performance, responsive SaaS platform designed for Labor Consultants and Certified Public Accountants (Commercialisti).

---

## 1. PROJECT OVERVIEW & VALUE PROPOSITION
The platform is a fast, responsive search and retrieval system. It allows professional consultants to quickly answer clients' practical accounting and invoicing doubts. It bridges the gap between official legal/fiscal sources (Agenzia delle Entrate, INPS, etc.) and practical software execution (how to log that specific transaction in ERPs like Zucchetti, TeamSystem, Danea, etc.).
Target response time for user queries: <500ms.

## 2. TECHNICAL STACK (RECOMMENDED)
- **Frontend:** React 19 (or Next.js 15 App Router), Tailwind CSS (v4 compatible), TypeScript. 100% Mobile-first responsive layout.
- **Backend:** Node.js (Fastify or Express) with TypeScript OR Python (FastAPI) for advanced NLP/RAG.
- **Database/Search Engine:** PostgreSQL (for relational data, users, logs) + pgvector OR Pinecone/Milvus for Vector Search (RAG implementation on official decrees).
- **Caching:** Redis for frequent queries and session management.

## 3. ARCHITECTURE & CORE MODULES

### MODULE A: Semantic & Keyword Search Engine (The Core)
- Implement a search bar featuring Natural Language Processing (NLP).
- The engine must parse complex query intents (e.g., "Fattura co-prodotta regime forfettario reverse charge").
- **Data Ingestion Pipeline Schema:**
  - Official Sources (API/Scraper): Agenzia delle Entrate (AdE) Circulars, INPS guidelines, Gazzetta Ufficiale.
  - Practical Layer: Mapping internal IDs to specific ERP software procedures.

### MODULE B: The "Raccordo" Data Structure (Normative-to-ERP Mapping)
Every search result must return a standardized JSON structure matching this model:
- `id`: UUID
- `title`: Short descriptive title of the accounting procedure.
- `normative_summary`: 3-line max plain language explanation.
- `official_sources`: Array of objects `[{ source_name: string, url: string, target_paragraph: string }]`.
- `electronic_invoicing_fields`: Object `{ tipo_documento: string (e.g., TD16), natura_iva: string (e.g., N6.3) }`.
- `erp_mapping`: Array of objects `[{ erp_name: string, step_by_step_guide: string[], notes: string }]`.

### MODULE C: Client Communication Generator
- A feature that converts any search result into a pre-formatted, polite email/WhatsApp snippet tailored for the end client.
- Include a "Copy to Clipboard" and "Send via Email" action dispatcher.

### MODULE D: Studio Administration & Analytics
- Multi-tenant workspace for Accounting Firms.
- **Search Audit Logs:** Track who searched what, when, and what response was given (crucial for internal firm quality control).

---

## 4. UI/UX REQUIREMENTS (TAILWIND CSS)
- **Design System:** High-density, professional UI. Clean typography, minimal noise. Dominant colors: Deep professional blues/slates (`#1e293b`), sharp contrasts for readability, accessible UI (WCAG AA).
- **Main Dashboard Layout:**
  - Sidebar: Recent searches, Saved procedures, Studio logs.
  - Main Panel: Huge centralized search bar (Google-style but with instant filters for ERP type or fiscal topic below it).
  - Results View: Split-screen or clear card-based hierarchy: Left = Law & FE Codes; Right = ERP Step-by-step guides.

---

## 5. STEP-BY-STEP IMPLEMENTATION PLAN REQUESTED
Please generate the initial boilerplate and structure following these steps:

### STEP 1: Database Schema & Models
Generate the Prisma Schema (or PostgreSQL SQL DDL) representing Users, Firms, SearchLogs, AccountingProcedures, and ErpMappings, ensuring correct foreign keys and indexes for performance.

### STEP 2: Backend API Routes (TypeScript/FastAPI)
Generate the API endpoints for:
- `GET /api/v1/search?q=...&erp=...` (Handling search logic, mocking the vector/keyword match response for now).
- `POST /api/v1/procedures` (To let admins add new guides).
- `GET /api/v1/logs/studio` (Fetch query history).

### STEP 3: Frontend Responsive Components (React/Tailwind)
Generate the following highly responsive components:
1. `SearchBar.tsx`: Accessible input with instant dropdown filters.
2. `ProcedureResultCard.tsx`: Tabbed component switching between "Normativa/Dati SDI" and "Configurazione Gestionale".
3. `ShareSnippetButton.tsx`: Handles dynamic formatting for client messaging.

### STEP 4: Mock Data Seed
Provide a comprehensive seed file (`seed.ts` or `seed.json`) containing at least 3 complex real-world Italian accounting examples (e.g., *Autofattura TD17 per servizi da Paese UE*, *Reverse Charge interno ex art.17*, *Registrazione Forfettario con bollo virtuale*).

---

## 6. CODING CONSTRAINTS
- Strict TypeScript: No `any`. Use descriptive interfaces.
- Clean Code: Modular components, custom hooks for fetching data.
- Tailwind CSS: Use standard semantic utility classes. Do not hardcode arbitrary values where theme tokens should be used.
- Performance: Write optimized SQL queries; ensure components do not trigger unnecessary re-renders.

Let's begin by generating **STEP 1 (Database Schema)** and the **API Routing structure (STEP 2)**.