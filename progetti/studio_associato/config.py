import os

# --- MOCK CREDENTIALS ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")
PORT = int(os.getenv("PORT", 8001))  # Run on port 8001 to avoid conflicting with the Hotel app

# --- CLIENTS DATABASE (312 firms total in mock system, showing a rich subset of 7 realistic ones) ---
AZIENDE_DB = [
    {
        "id": "sacorona_vino",
        "denominazione": "Cantine Sa Corona S.r.l.",
        "ateco": "11.02.10",
        "ateco_desc": "Produzione di vini da uve prodotte in aziende agricole",
        "sede": "Serdiana (CA)",
        "fatturato_2025": 4500000.0,
        "dipendenti": 24,
        "dimensione": "PMI",
        "eta_titolare": 52,
        "area_zes": False,
        "email_referente": "direzione@sacorona-vino.it",
        "telefono_referente": "+39 348 7654321",
        "referente": "Dott. Franco Corona"
    },
    {
        "id": "barbagia_pastori",
        "denominazione": "Cooperativa Barbagia Pastori",
        "ateco": "01.45.00",
        "ateco_desc": "Allevamento di ovini e caprini",
        "sede": "Fonni (NU)",
        "fatturato_2025": 850000.0,
        "dipendenti": 8,
        "dimensione": "Micro",
        "eta_titolare": 34,
        "area_zes": False,
        "email_referente": "m.loddo@barbagiapastori.it",
        "telefono_referente": "+39 333 1234567",
        "referente": "Michele Loddo"
    },
    {
        "id": "sardinia_tech",
        "denominazione": "Sardinia Tech Solutions S.r.l.",
        "ateco": "62.01.00",
        "ateco_desc": "Produzione di software non personalizzato",
        "sede": "Area Industriale Elmas (CA)",
        "fatturato_2025": 1200000.0,
        "dipendenti": 14,
        "dimensione": "Micro",
        "eta_titolare": 29,
        "area_zes": True,
        "email_referente": "a.sanna@sardiniatech.io",
        "telefono_referente": "+39 349 9876543",
        "referente": "Ing. Alessandro Sanna"
    },
    {
        "id": "hotel_antigaluna",
        "denominazione": "Boutique Hotel Antiga Luna Charme & Spa",
        "ateco": "55.10.00",
        "ateco_desc": "Alberghi e strutture simili",
        "sede": "Domus de Maria (SU)",
        "fatturato_2025": 1800000.0,
        "dipendenti": 18,
        "dimensione": "PMI",
        "eta_titolare": 45,
        "area_zes": False,
        "email_referente": "m.ferru@hotel-antigaluna.it",
        "telefono_referente": "+39 340 1122334",
        "referente": "Marianna Ferru"
    },
    {
        "id": "pastificio_armonia",
        "denominazione": "Pastificio Artigianale Antiga Armonia",
        "ateco": "10.73.00",
        "ateco_desc": "Produzione di paste alimentari, di cuscus e di prodotti farinacei simili",
        "sede": "Tempio Pausania (SS)",
        "fatturato_2025": 320000.0,
        "dipendenti": 3,
        "dimensione": "Micro",
        "eta_titolare": 39,
        "area_zes": False,
        "email_referente": "g.mu@pastificioantigaarmonia.it",
        "telefono_referente": "+39 328 4455667",
        "referente": "Giovanni Mu"
    },
    {
        "id": "officine_macc_sarde",
        "denominazione": "Officine Meccaniche Sarde S.r.l.",
        "ateco": "25.62.00",
        "ateco_desc": "Lavorazione di metalli e meccanica generale",
        "sede": "Zona Industriale Tossilo - Macomer (NU)",
        "fatturato_2025": 2100000.0,
        "dipendenti": 22,
        "dimensione": "PMI",
        "eta_titolare": 48,
        "area_zes": True,
        "email_referente": "produzione@officinemeccanichesarde.it",
        "telefono_referente": "+39 347 5566778",
        "referente": "Ing. Pietro Meloni"
    },
    {
        "id": "agriturismo_antigaluna",
        "denominazione": "Agriturismo Antiga Luna S.r.l.",
        "ateco": "56.10.12",
        "ateco_desc": "Attività di ristorazione connesse alle aziende agricole (Agriturismi)",
        "sede": "Oliena (NU)",
        "fatturato_2025": 1500000.0,
        "dipendenti": 12,
        "dimensione": "PMI",
        "eta_titolare": 62,
        "area_zes": False,
        "email_referente": "prenotazioni@antigaluna-agriturismo.it",
        "telefono_referente": "+39 335 9988776",
        "referente": "Elena Contini"
    }
]

# --- REGIONAL GRANTS DATABASE (Bandi indicizzati nel sistema RAG) ---
BANDI_DB = [
    {
        "id": "por_fesr_pmi",
        "titolo": "POR FESR Sardegna 2021-2027 — Bando Digitalizzazione delle PMI",
        "categoria": "Digitalizzazione & Innovazione",
        "descrizione": "Finanziamento a sostegno di investimenti per l'acquisizione di servizi informatici, software, soluzioni cloud, cybersecurity, e-commerce e sistemi di intelligenza artificiale per l'ottimizzazione aziendale.",
        "contributo": "65% a fondo perduto sulle spese ammissibili",
        "investimento_min": 15000.0,
        "finanziamento_max": 150000.0,
        "scadenza": "2026-10-15",
        "ateco_ammessi": ["10", "11", "25", "45", "47", "55", "56", "62", "79"],
        "requisiti_dimensione": ["Micro", "PMI"],
        "richiede_zes": False,
        "richiede_giovani": False
    },
    {
        "id": "psr_giovani_agri",
        "titolo": "PSR Sardegna — Premio per l'insediamento di Giovani Agricoltori (Misura 6.1)",
        "categoria": "Agricoltura & Allevamento",
        "descrizione": "Premio forfettario a fondo perduto per favorire il ricambio generazionale in agricoltura, incentivando l'insediamento di giovani imprenditori agricoli qualificati sul territorio sardo.",
        "contributo": "€ 50.000 una tantum a fondo perduto",
        "investimento_min": 0.0,
        "finanziamento_max": 50000.0,
        "scadenza": "2026-09-30",
        "ateco_ammessi": ["01"],
        "requisiti_dimensione": ["Micro", "PMI"],
        "richiede_zes": False,
        "richiede_giovani": True  # Titolare con età < 41 anni
    },
    {
        "id": "zes_unica_sardegna",
        "titolo": "ZES Unica — Credito d'Imposta per Investimenti Produttivi in Sardegna",
        "categoria": "Fiscale & Investimenti Industriali",
        "descrizione": "Agevolazione fiscale sotto forma di credito d'imposta per l'acquisizione di beni strumentali, macchinari, impianti innovativi e l'acquisto di terreni o l'acquisizione di immobili destinati a insediamenti produttivi situati nelle aree ZES sarde.",
        "contributo": "Fino al 45% di credito d'imposta sull'investimento",
        "investimento_min": 50000.0,
        "finanziamento_max": 200000.0,
        "scadenza": "2026-12-31",
        "ateco_ammessi": ["10", "11", "25", "55", "62"],  # Escluso agricoltura primaria e commercio al dettaglio puro
        "requisiti_dimensione": ["Micro", "PMI", "Grande"],
        "richiede_zes": True,  # La sede deve trovarsi in area ZES
        "richiede_giovani": False
    },
    {
        "id": "misura_cooperazione_filiera",
        "titolo": "PSR Sardegna — Cooperazione di Filiera per Innovazione Agroalimentare (Misura 16.2)",
        "categoria": "Agroalimentare & Filiera",
        "descrizione": "Finanziamento a sostegno di progetti pilota di cooperazione tra aziende agricole, trasformatrici e distributrici sarde per lo sviluppo di nuovi prodotti artigianali, processi ecologici e filiere corte e tracciabili.",
        "contributo": "80% a fondo perduto sulle spese complessive di progetto",
        "investimento_min": 100000.0,
        "finanziamento_max": 300000.0,
        "scadenza": "2026-11-20",
        "ateco_ammessi": ["01", "10", "11"],
        "requisiti_dimensione": ["Micro", "PMI"],
        "richiede_zes": False,
        "richiede_giovani": False
    }
]
