# Aijò — Consulente AI Sardegna — CLAUDE.md

## Progetto
Landing page e sito istituzionale di Marco Ferrara come consulente AI per le imprese sarde. Dominio: `aijo-consulenteai.it` (nessun dominio `aijo.ai` posseduto).

## Stack
- **Frontend:** HTML5 + CSS3 + JavaScript vanilla (no framework)
- **Deploy:** GitHub Pages (workflow `.github/workflows/deploy.yml`, push su `main`)
- **Dominio:** `www.aijo-consulenteai.it` — registrato/hostato su Aruba, puntato a GitHub Pages via `CNAME`
- **Form contatti:** Web3Forms (endpoint `api.web3forms.com`)
- **Asset:** SVG favicon, immagini OG

## File principali
```
index.html              # Pagina principale (landing)
index_maintenance.html  # Pagina di manutenzione
favicon.svg
assets/                 # Immagini e risorse statiche
progetti/               # Sotto-progetti clienti (vedi sotto)
```

## Sotto-progetti clienti
Ogni cartella in `progetti/` è un sito/app per un cliente specifico:
- `ricerca_commercialista/` — **LexDocs** (Next.js 15, vedi suo CLAUDE.md)
- `antiga_armonia/` — Python/Flask + Docker
- `boutique_hotel/`, `cantina_vinicola/`, `il_campanellino/`, `la_sorgente/`, `laboratorio_artistico/`, `logistica/`, `meneesco/`, `ricambi_truck/`, `social_pesca/`, `studio_associato/` — siti/app clienti vari

## Deploy landing page
Il sito è deployato su **GitHub Pages**: il workflow `.github/workflows/deploy.yml` pubblica l'intera root del repo a ogni push su `main`. Dominio `www.aijo-consulenteai.it` (Aruba) collegato tramite file `CNAME`. I contatti passano da **Web3Forms** (`action="https://api.web3forms.com/submit"`).

## Pagine SEO dedicate (città / intento)
Pagine statiche separate per intercettare query specifiche, senza toccare il testo della home:
- `intelligenza-artificiale-cagliari/`, `intelligenza-artificiale-sassari/` — local SEO per città
- `integrare-intelligenza-artificiale-azienda/` — pagina informativa "come integrare l'AI"
- Stile condiviso in `assets/seo-pages.css`. Ogni pagina ha JSON-LD (Service/Article + BreadcrumbList + FAQPage), va aggiunta a `sitemap.xml` e linkata internamente.

## Convenzioni
- Commenti HTML/JS in italiano
- Indentazione 2 spazi
- Conventional commits in italiano
