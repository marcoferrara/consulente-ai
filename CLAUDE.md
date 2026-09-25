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
demo/                   # Demo statiche aperte dalla landing (studio_associato, cantina_vinicola, laboratorio_artistico, logistica)
```

## Progetti clienti (fuori da questa cartella)
Tutti i progetti clienti vivono come cartelle sorelle in `C:\Users\marco\Claude Code\` (non più in `progetti/`), ognuno col suo CLAUDE.md dove presente:
- `ricerca_commercialista/` — **LexDocs** (Next.js 15)
- `antiga_armonia/` — Python/Flask + Docker
- `accademia_internazionale_musical/`, `ail/`, `boutique_hotel/`, `bw-charter/` (ha un proprio repo git), `il_campanellino/`, `la_sorgente/`, `meneesco/`, `social_pesca/`, `vendite-dashboard/` — siti/app clienti vari
- Le demo in `demo/` restano qui perché la landing le apre con link relativi (`demo/<nome>/index.html`); `laboratorio_artistico` e `logistica` tornano alla home con `../../index.html`

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
