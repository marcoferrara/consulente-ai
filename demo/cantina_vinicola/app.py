import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from config import GEMINI_API_KEY, PORT, WINERY_BIO, WINERY_NAME

# ---------------------------------------------------------------------------
# Load database
# ---------------------------------------------------------------------------
DB_PATH = Path(__file__).parent / "database.json"
with open(DB_PATH, encoding="utf-8") as f:
    DB = json.load(f)

# ---------------------------------------------------------------------------
# Gemini setup (optional)
# ---------------------------------------------------------------------------
gemini_available = False
gemini_model = None

if GEMINI_API_KEY:
    try:
        import google.generativeai as genai

        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        gemini_available = True
    except Exception as e:
        print(f"[WARN] Gemini not available: {e}")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="Tenute Ichnos – Export Intelligence Suite", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class LocalizeRequest(BaseModel):
    wine_id: str
    market: str  # "usa" | "germany"


class NewsletterRequest(BaseModel):
    wine_id: str
    market: str  # "usa" | "germany"
    importer_name: str
    tone: str  # "formal" | "warm"
    occasion: str  # "catalog" | "harvest" | "seasonal"


class SentimentRequest(BaseModel):
    wine_id: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_wine_or_404(wine_id: str) -> dict:
    wine = DB["wines"].get(wine_id)
    if not wine:
        raise HTTPException(status_code=404, detail=f"Wine '{wine_id}' not found")
    return wine


def get_reviews(wine_id: str) -> list:
    return DB["reviews"].get(wine_id, [])


def call_gemini(prompt: str) -> str:
    """Call Gemini and return raw text response."""
    response = gemini_model.generate_content(prompt)
    return response.text


def extract_json_from_response(text: str) -> dict:
    """Extract JSON from a Gemini response that may contain markdown fences."""
    import re

    # Try to find ```json ... ``` block
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    # Try to find raw JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError("No JSON found in Gemini response")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
def serve_index():
    index_path = Path(__file__).parent / "index.html"
    return FileResponse(str(index_path))


@app.get("/api/wines")
def list_wines():
    return JSONResponse(
        {
            "winery": DB["winery"],
            "wines": [
                {
                    "id": w["id"],
                    "name": w["name"],
                    "full_name": w["full_name"],
                    "denomination": w["denomination"],
                    "vintage": w["vintage"],
                    "alcohol": w["alcohol"],
                    "trade_price_eur": w["trade_price_eur"],
                    "bottles_produced": w["bottles_produced"],
                    "target_markets": w["target_markets"],
                    "aging_potential_years": w["aging_potential_years"],
                    "tasting_notes_it": w["tasting_notes_it"],
                    "food_pairing_it": w["food_pairing_it"],
                    "grape": w["grape"],
                    "vine_age_years": w["vine_age_years"],
                    "harvest": w["harvest"],
                    "vinification": w["vinification"],
                }
                for w in DB["wines"].values()
            ],
        }
    )


@app.get("/api/reviews/{wine_id}")
def get_wine_reviews(wine_id: str):
    get_wine_or_404(wine_id)
    reviews = get_reviews(wine_id)
    return JSONResponse({"wine_id": wine_id, "reviews": reviews, "count": len(reviews)})


# ---------------------------------------------------------------------------
# POST /api/localize
# ---------------------------------------------------------------------------
@app.post("/api/localize")
def localize_wine(req: LocalizeRequest):
    wine = get_wine_or_404(req.wine_id)
    market = req.market.lower()

    if market not in ("usa", "germany"):
        raise HTTPException(status_code=400, detail="market must be 'usa' or 'germany'")

    if gemini_available:
        try:
            result = _localize_with_gemini(wine, market)
            return JSONResponse({"source": "gemini", "market": market, "data": result})
        except Exception as e:
            print(f"[WARN] Gemini localize failed: {e}")

    # Fallback mock
    result = _localize_mock(wine, market)
    return JSONResponse({"source": "mock", "market": market, "data": result})


def _localize_with_gemini(wine: dict, market: str) -> dict:
    winery = DB["winery"]
    tn = wine["tasting_notes_it"]

    if market == "usa":
        market_instructions = """
TARGET MARKET: United States of America
AUDIENCE: American wine importers, sommeliers, and premium wine retail buyers.

ADAPTATION RULES — apply ALL of these:
1. STORYTELLING ANGLE — "Longevity & Blue Zone": Emphasize that Jerzu/Ogliastra is in one of only five Blue Zones on Earth, where people live past 100. Frame the wine as an expression of a land of longevity. Make this the emotional anchor of the storytelling paragraph.
2. LANGUAGE TONE: Passionate, direct, confident. Americans love a great origin story. Use vivid sensory language.
3. FOOD PAIRING: Adapt to American cuisine — dry-aged steakhouse cuts, BBQ brisket and ribs, Thanksgiving roasts, Italian-American Sunday dinner. Be specific and appetizing.
4. HERITAGE: Emphasize the 4-generation family story (since 1932) — Americans deeply value family legacy in artisan products.
5. VALUE FRAMING: Position as "the discovery wine" — world-class quality that most Americans haven't found yet.
6. LABEL COPY: Short, punchy, suitable for an American wine shelf card. Under 25 words.
7. TECH HIGHLIGHTS: 3-4 bullet points with key facts American buyers care about (alcohol level, aging potential in years, production size, vine age).
"""
    else:  # germany
        market_instructions = """
TARGET MARKET: Germany (Deutschland)
AUDIENCE: German wine importers (Weinhändler), restaurateurs (Gastronomen), and sophisticated wine collectors (Weinsammler).

ADAPTATION RULES — apply ALL of these:
1. TONE: Technical, precise, informative. German buyers expect exactness and substantiation. No hyperbole without data.
2. TERROIR FOCUS: Describe the granite soil of Ogliastra (Granit aus dem Ogliastra-Gebirge), altitude range (350–620 m), diurnal temperature variation (15–18°C). Use specific geological and climatic data.
3. STRUCTURAL COMPARISON: Compare tannin structure and body to wines Germans know — Spätburgunder (Pinot Noir), Blauburgunder, Châteauneuf-du-Pape. Be analytical.
4. AGING POTENTIAL: State exact years of cellaring potential. Germans are collectors; give them a precise maturity window (e.g., "optimal 2026–2032").
5. VITICULTURE: Mention vine age in years, yield in hl/ha, harvest method — these data points matter to German professionals.
6. FOOD PAIRING: German cuisine references — Wildragout, geschmortes Lamm, Hartkäse, Rinderschmorbraten. Be culturally specific.
7. LABEL COPY: Elegant, classical, suitable for a German Weinhandlung shelf card. Under 25 words.
8. TECH HIGHLIGHTS: 4-5 precise bullet points with all technical data (Alkohol, Ertrag, Rebenalter, Reifepotenzial, Böden).
"""

    prompt = f"""You are an expert wine content writer specializing in cultural adaptation for international markets.

WINERY: {winery['name']} — {winery['location']} — Founded {winery['founded']}
WINERY BIO: {winery['bio']}
SOIL: {winery['soil']} | ALTITUDE: {winery['altitude_range_m']} m | CLIMATE: {winery['climate']}

WINE TO ADAPT:
- Name: {wine['full_name']}
- Grape: {wine['grape']}
- Vintage: {wine['vintage']}
- Alcohol: {wine['alcohol']}%
- Production: {wine['bottles_produced']:,} bottles
- Vine age: {wine['vine_age_years']} years
- Yield: {wine['yield_hl_ha']} hl/ha
- Harvest: {wine['harvest']}
- Vinification: {wine['vinification']}
- Aging potential: {wine['aging_potential_years']} years
- Original Italian tasting notes:
  Color: {tn['color']}
  Nose: {tn['nose']}
  Palate: {tn['palate']}
  Finish: {tn['finish']}
- Original Italian food pairing: {wine['food_pairing_it']}

{market_instructions}

CRITICAL: Return ONLY a valid JSON object — no markdown, no explanation, no extra text.
The JSON must have exactly these keys:
{{
  "adapted_title": "string — localized wine name/title for this market",
  "tagline": "string — one evocative sentence, the emotional hook for this market",
  "tasting_notes": "string — 3-4 sentences, adapted sensory description for this market's palate vocabulary",
  "food_pairing": "string — 3-5 culturally specific food pairing suggestions for this market",
  "storytelling_paragraph": "string — 4-5 sentences, the full brand story adapted for this market (use the specific cultural angle)",
  "label_copy": "string — short shelf card text, under 25 words, punchy and market-specific",
  "tech_highlights": ["string", "string", "string", "string"]
}}
"""

    raw = call_gemini(prompt)
    return extract_json_from_response(raw)


def _localize_mock(wine: dict, market: str) -> dict:
    if market == "usa":
        if wine["id"] == "cannonau_riserva":
            return {
                "adapted_title": "Antico Cannonau Reserve — A Wine from the Land of the Centenarians",
                "tagline": "Born in Sardinia's Blue Zone, where ancient vines and timeless traditions craft wines as enduring as the people who tend them.",
                "tasting_notes": "Deep ruby red with garnet hues. The nose opens with wild blackberry, myrtle berry, and dried fig — signature flavors of the sun-drenched Ogliastra hills. On the palate, velvety tannins frame ripe plum, black cherry jam, and a whisper of espresso. The finish lingers long with dark chocolate and fresh Mediterranean herbs.",
                "food_pairing": "Dry-aged ribeye at your favorite steakhouse, slow-smoked BBQ brisket, Sunday lamb roast, hearty Italian-American braised short ribs, aged Parmigiano-Reggiano.",
                "storytelling_paragraph": "The Ogliastra region of Sardinia is one of only five Blue Zones on Earth — places where people routinely live past 100. The Sechi family has been tending these ancient granite hillsides since 1932, four generations pouring their soul into every bottle. The 45-year-old Cannonau vines here don't just produce wine; they express a philosophy of patience, quality, and deep respect for the land. 'Antico' — meaning 'ancient' — is their finest expression: a Reserve wine that carries the longevity of the people and the land into every glass.",
                "label_copy": "Four generations. One Blue Zone. Sardinia's most celebrated Cannonau Reserve.",
                "tech_highlights": [
                    "14.5% ABV — full-bodied and structured",
                    "Aged 18 months in French oak + 12 months bottle rest",
                    "Only 8,000 bottles produced — limited allocation",
                    "Drinking window: now through 2034",
                ],
            }
        elif wine["id"] == "vermentino_docg":
            return {
                "adapted_title": "Alios Vermentino — Sardinia's Crown Jewel White",
                "tagline": "Harvested by night on ancient Mediterranean granite, this DOCG white is the ocean breeze in a glass.",
                "tasting_notes": "Bright straw yellow with vivid green reflections. Explosive aromatics: grapefruit, bergamot, white peach, and sea-washed pebbles. The palate is alive with salinity and citrus zest, finishing with a distinctive bitter almond signature unique to this ancient Sardinian grape variety.",
                "food_pairing": "Grilled jumbo shrimp, seafood towers, fresh oysters on the half shell, Thai green curry, light ceviche, sushi and sashimi platters.",
                "storytelling_paragraph": "Vermentino di Gallura is the only DOCG white wine from Sardinia — Italy's most rigorous quality designation. Tenute Ichnos' 'Alios' is harvested at night to protect its precious aromatics from the Mediterranean heat, then aged on its fine lees for complexity and texture. The result is a white wine with serious personality: salty, vivid, and utterly unique. If you love Sauvignon Blanc, Chablis, or Albariño, 'Alios' will become your new obsession.",
                "label_copy": "Italy's only DOCG white from Sardinia. Night-harvested for pure, unforgettable aromatics.",
                "tech_highlights": [
                    "13% ABV — elegant and food-friendly",
                    "Night harvest preserves full aromatic profile",
                    "4 months sur lies — extra texture and complexity",
                    "Best enjoyed: 2023–2026",
                ],
            }
        else:
            return {
                "adapted_title": "Mastio Carignan — Sardinia's Old Vines Secret",
                "tagline": "Sixty-year-old vines tell no lies — only pure fruit, ancient soil, and the quiet wisdom of centuries.",
                "tasting_notes": "Vivid ruby with violet flashes. Bright red berry fruit — raspberry, pomegranate, fresh cherry — with lavender and wild herbs. The palate is energetic and precise, with silky tannins from 60-year-old bush vines. A wine of joy and depth in equal measure.",
                "food_pairing": "Wood-fired pizza, charcuterie boards, roasted pork tenderloin, mushroom risotto, medium-aged sheep's milk cheese.",
                "storytelling_paragraph": "When grapevines are trained as individual bushes — the ancient 'alberello' method — and left to grow for 60 years, something extraordinary happens. Their roots reach deep into Sardinian volcanic soil, drawing minerals and character that younger vines simply cannot. Mastio is Tenute Ichnos' love letter to this tradition: a wine of remarkable elegance and approachability, produced from some of the oldest Carignan vines in Italy.",
                "label_copy": "60-year-old bush vines. No new oak. Pure Sardinian soul.",
                "tech_highlights": [
                    "13.5% ABV — balanced and elegant",
                    "Aged in large Slavonian oak barrels — zero new oak influence",
                    "60-year-old alberello (bush-trained) vines",
                    "Only 6,000 bottles — a true collector's wine",
                ],
            }
    else:  # germany
        if wine["id"] == "cannonau_riserva":
            return {
                "adapted_title": "Antico — Cannonau di Sardegna DOC Riserva",
                "tagline": "Granit, Meereswind und vier Generationen Können: der tiefste Ausdruck des ogliastresischen Terroirs.",
                "tasting_notes": "Tiefes Rubinrot mit Granatnuancen. Die Nase zeigt dichte Aromatik aus schwarzen Waldbeeren, Lakritze und mediterranen Kräutern (Myrte, Lentiscus). Am Gaumen dichtes, seidiges Tanningerüst — vergleichbar einem großen Châteauneuf-du-Pape, jedoch mit unverkennbarer sardischer Salzmineralität. Der Abgang ist außergewöhnlich lang, mit Kakao und wilder Minze.",
                "food_pairing": "Wildragout mit Preiselbeeren, geschmortes Lamm mit Rosmarin, Rinderschmorbraten, kräftiger Hartkäse (Pecorino stagionato, Comté), dunkle Schokoladenspezialitäten.",
                "storytelling_paragraph": "Die Tenute Ichnos liegt in Jerzu, Ogliastra — einem der wenigen Gebiete der Welt, in denen der Granit des Grundgebirges auf 350 bis 620 Metern Höhe einen einzigartigen Terroir-Ausdruck schafft. Die tägliche Temperaturschwankung von 15–18°C sorgt für perfekte Aromatik und Säurestruktur. Mit einem Ertrag von nur 28 hl/ha und 45-jährigen Rebstöcken erzeugt Familie Sechi seit 1932 Weine, die die Langlebigkeit ihres Landes widerspiegeln — Ogliastra ist eine der fünf Blue Zones der Erde. Der 'Antico' 2019 zeigt seine optimale Trinkreife zwischen 2026 und 2034.",
                "label_copy": "Granit-Terroir · 45-jährige Reben · 18 Monate Barrique · Trinkreife bis 2034.",
                "tech_highlights": [
                    "Alkohol: 14,5 % vol.",
                    "Ertrag: 28 hl/ha — Konzentration durch natürliche Limitierung",
                    "Rebenalter: 45 Jahre — komplexere Polyphenolstruktur",
                    "Reifung: 18 Monate Barrique (30% neu) + 12 Monate Flasche",
                    "Lagerpotenzial: optimal 2026–2034, maximal bis 2038",
                ],
            }
        elif wine["id"] == "vermentino_docg":
            return {
                "adapted_title": "Alios — Vermentino di Gallura DOCG",
                "tagline": "Nachtlese auf sardischem Granit: Präzision, Salinität und mediterrane Frische in ihrer reinsten Form.",
                "tasting_notes": "Helles Strohgelb mit lebhaften Grünreflexen. Aromatisch präzise: Grapefruit, Bergamotte, Weißdorn, Kräuter der Macchia. Am Gaumen erinnert die Säurestruktur an einen Mosel-Riesling Spätlese, jedoch mit deutlich mediterranem, salinitätsreichem Charakter. Die sur-lies-Reifung gibt eine cremige Textur ohne Frischeopfer. Mineralischer, leicht bittermandeliger Abgang — typisch für die Gallura-DOCG.",
                "food_pairing": "Nordseeaustern und Meeresfrüchte, Zanderfilet mit Kapernbutter, frischer Ziegenkäse, leichtes Ceviche, gedämpfter Steinbutt.",
                "storytelling_paragraph": "Der Vermentino di Gallura ist die einzige DOCG-Weißweinkategorie Sardiniens — Italiens strengste Qualitätskategorie. Tenute Ichnos' Alios entsteht aus Nachtlese (fine agosto/settembre), um die flüchtigen Aromastoffe zu schonen, gefolgt von 4 Monaten auf den feinen Hefen mit wöchentlichem Bâtonnage. Das Ergebnis: ein technisch tadelloser Wein mit außergewöhnlicher Mineralität und Frische. Für Liebhaber von Burgund-Weißweinen oder elsässischem Riesling ein unverzichtbarer Entdeckungswein.",
                "label_copy": "DOCG Gallura · Nachtlese · sur lies · Granit-Terroir · trinkreif 2023–2026.",
                "tech_highlights": [
                    "Alkohol: 13,0 % vol.",
                    "Nachtlese Ende August — Schutz der Aromaintegrität",
                    "4 Monate sur lies mit Bâtonnage — Textur und Komplexität",
                    "Trinkreife: optimal jetzt bis 2026",
                    "15.000 Flaschen — breit verfügbar für Gastronomie",
                ],
            }
        else:
            return {
                "adapted_title": "Mastio — Carignano del Sulcis DOC",
                "tagline": "60-jährige Alberello-Reben, großes Holz, Null Kompromisse — Sardiniens eleganteste Rarität.",
                "tasting_notes": "Lebhaftes Rubinrot mit violetten Reflexen. Nase: rote Früchte (Kirsche, Himbeere, Granatapfel), Veilchen, Lavendel, ein Hauch von Schiefer. Am Gaumen elegant und dynamisch — ähnlich einem Burgund oder einem feinen Pinot Noir aus dem Elsass, jedoch mit wärmerem Fruchtprofil. Tannine seidig und präzise, Säure knackig und lang.",
                "food_pairing": "Geschmorter Lammrücken mit Kräutern, Wildschweingulasch, halbgereifter Schafskäse, Antipasti-Platten, leichte Pasta mit Tomatensauce.",
                "storytelling_paragraph": "Das Sulcis im Südwesten Sardiniens beherbergt einige der ältesten Alberello-gepflanzten Carignano-Reben der Welt. Tenute Ichnos' 'Mastio' stammt aus 60-jährigen Rebstöcken mit einem Ertrag von nur 22 hl/ha. Die Vinifikation erfolgt in Zementsektoren ohne Temperaturregelung, die Reifung in 50-hl-Slavonia-Botti — kein neues Holz, keine Überextraktion. Das Ergebnis ist ein Wein von seltener Eleganz und Trinkfreude, der Liebhaber von Burgund und Norditalien ansprechen wird. Lagerpotenzial 2025–2030.",
                "label_copy": "60 Jahre Alberello · Zement · Slavonia-Botte · Lagerpotenzial bis 2030.",
                "tech_highlights": [
                    "Alkohol: 13,5 % vol.",
                    "Ertrag: 22 hl/ha — extreme Konzentration alter Reben",
                    "Rebenalter: 60 Jahre — Alberello-Erziehung",
                    "Reifung: 12 Monate Slavonia-Botte (50 hl) — kein neues Eichenholz",
                    "Lagerpotenzial: optimal 2025–2030, maximal 2033",
                ],
            }


# ---------------------------------------------------------------------------
# POST /api/newsletter
# ---------------------------------------------------------------------------
@app.post("/api/newsletter")
def generate_newsletter(req: NewsletterRequest):
    wine = get_wine_or_404(req.wine_id)
    market = req.market.lower()

    if market not in ("usa", "germany"):
        raise HTTPException(status_code=400, detail="market must be 'usa' or 'germany'")

    if gemini_available:
        try:
            result = _newsletter_with_gemini(wine, market, req)
            return JSONResponse({"source": "gemini", "market": market, "data": result})
        except Exception as e:
            print(f"[WARN] Gemini newsletter failed: {e}")

    result = _newsletter_mock(wine, market, req)
    return JSONResponse({"source": "mock", "market": market, "data": result})


def _newsletter_with_gemini(wine: dict, market: str, req: NewsletterRequest) -> dict:
    winery = DB["winery"]
    lang = "English" if market == "usa" else "German (Deutsch)"
    tone_desc = (
        "professional and formal, suitable for high-level B2B communication"
        if req.tone == "formal"
        else "warm, personable, and relationship-focused while remaining professional"
    )

    occasion_map = {
        "catalog": (
            "Catalog Presentation — introducing the winery's portfolio to a new importer",
            "Katalogvorstellung — Vorstellung des Weingut-Portfolios bei einem neuen Importeur",
        ),
        "harvest": (
            "Harvest Announcement — sharing news about the latest vintage and harvest conditions",
            "Erntebericht — Mitteilung über die neueste Ernte und Jahrgangsqualität",
        ),
        "seasonal": (
            "Seasonal Offer — a targeted commercial offer for the upcoming season",
            "Saisonangebot — ein gezieltes kommerzielles Angebot für die kommende Saison",
        ),
    }
    occasion_en, occasion_de = occasion_map.get(req.occasion, occasion_map["catalog"])
    occasion_desc = occasion_en if market == "usa" else occasion_de

    prompt = f"""You are an expert B2B wine marketing copywriter for premium Italian wineries.

Write a professional B2B email newsletter in {lang} for the following:

WINERY: {winery['name']} — {winery['location']}
WINERY BIO: {winery['bio']}
RECIPIENT: {req.importer_name} (wine importer)
FEATURED WINE: {wine['full_name']}, vintage {wine['vintage']}
WINE DESCRIPTION: {wine['tasting_notes_it']['nose']}. {wine['tasting_notes_it']['palate']}
TRADE PRICE: €{wine['trade_price_eur']:.2f} per bottle
OCCASION: {occasion_desc}
TONE: {tone_desc}

REQUIREMENTS:
- Write entirely in {lang}
- Subject line: compelling, professional, under 60 characters
- Preheader: 1 sentence summary, under 100 characters
- Body: 4-6 paragraphs, structured as: greeting → story/occasion → wine details → commercial proposition → call to action → sign-off
- Use **bold** for important words/phrases (the renderer will interpret this)
- Use \\n\\n between paragraphs
- CTA: a clear, specific call to action text (e.g. "Request your allocation" or "Jetzt Muster anfordern")
- Keep it under 400 words total in the body

CRITICAL: Return ONLY a valid JSON object with these exact keys:
{{
  "subject": "string",
  "preheader": "string",
  "body_html": "string (use **bold** and \\n\\n for paragraphs, NO real HTML tags)",
  "cta_text": "string"
}}
"""

    raw = call_gemini(prompt)
    return extract_json_from_response(raw)


def _newsletter_mock(wine: dict, market: str, req: NewsletterRequest) -> dict:
    importer = req.importer_name or "Dear Partner"

    if market == "usa":
        occasion_subjects = {
            "catalog": f"Introducing Tenute Ichnos — Sardinia's Hidden Gem for Your Portfolio",
            "harvest": f"2023 Harvest Report — Exceptional Year at Tenute Ichnos, Sardinia",
            "seasonal": f"Spring Allocation Available — Tenute Ichnos Limited Releases",
        }
        subject = occasion_subjects.get(req.occasion, occasion_subjects["catalog"])
        return {
            "subject": subject,
            "preheader": "A four-generation Sardinian winery from one of Earth's five Blue Zones.",
            "body_html": f"Dear {importer},\n\nI hope this message finds you well. My name is Marco Sechi, and I represent **Tenute Ichnos**, a family winery in **Jerzu, Ogliastra** — the heart of Sardinia's legendary Blue Zone, one of only five places on Earth where people routinely live past 100.\n\nWe have been cultivating our 45 hectares of ancient granite hillsides since **1932**, and today I am delighted to introduce you to our flagship wine: **{wine['full_name']}, {wine['vintage']}**.\n\nThis is a wine that tells the story of our land. At **€{wine['trade_price_eur']:.2f} trade price per bottle**, it represents extraordinary value for a wine of this heritage and quality — {wine['aging_potential_years']} years aging potential, only **{wine['bottles_produced']:,} bottles produced**.\n\nWe are currently looking for **exclusive import partners** in the United States who share our passion for authentic, family-produced Italian wines. Our wines have been discovered by leading sommeliers and are generating significant buzz among wine enthusiasts on platforms like Vivino.\n\nI would be delighted to arrange a complimentary sample shipment and discuss allocation terms. Our export manager will be attending **Vinexpo New York** this spring and would welcome the opportunity to meet.\n\nWarm regards,\n**Marco Sechi**\nExport Director, Tenute Ichnos\nJerzu, Ogliastra — Sardegna, Italy",
            "cta_text": "Request Your Sample Allocation",
        }
    else:  # germany
        occasion_subjects = {
            "catalog": f"Tenute Ichnos — Sardiniens außergewöhnlichste Erzeugnisse für Ihr Portfolio",
            "harvest": f"Erntebericht 2023 — Außergewöhnlicher Jahrgang bei Tenute Ichnos",
            "seasonal": f"Frühjahrsallokation verfügbar — Tenute Ichnos limitierte Weine",
        }
        subject = occasion_subjects.get(req.occasion, occasion_subjects["catalog"])
        return {
            "subject": subject,
            "preheader": "Vier Generationen, 45 Hektar Granit-Terroir, Blue Zone Ogliastra.",
            "body_html": f"Sehr geehrte Damen und Herren, liebe/r {importer},\n\nmein Name ist Marco Sechi, und ich vertrete **Tenute Ichnos**, ein Familienweingut in **Jerzu, Ogliastra** — im Herzen einer der fünf Blue Zones der Erde, wo Menschen regelmäßig über 100 Jahre alt werden.\n\nSeit **1932** bewirtschaften wir 45 Hektar auf 350–620 Metern Höhe im ogliastresischen Granit-Gebirge. Heute möchte ich Ihnen unseren Flaggschiff-Wein vorstellen: **{wine['full_name']}, Jahrgang {wine['vintage']}**.\n\nDieser Wein entsteht aus **{wine['vine_age_years']}-jährigen Rebstöcken** bei einem Ertrag von nur **{wine['yield_hl_ha']} hl/ha** — eine natürliche Konzentration, die den Charakter des Terroirs unverfälscht widerspiegelt. Der **Handelspreis beträgt €{wine['trade_price_eur']:.2f} pro Flasche** bei einer Produktion von nur **{wine['bottles_produced']:,} Flaschen**.\n\nWir suchen **qualifizierte Importpartner** im deutschsprachigen Raum mit Zugang zum Fachhandel und zur Spitzengastronomie. Unsere Weine überzeugen durch technische Präzision, terroir-treuen Ausdruck und hervorragendes Preis-Leistungs-Verhältnis.\n\nGerne senden wir Ihnen ein kostenloses Verkostungsmuster zu und senden Ihnen unsere detaillierten technischen Datenblätter. Wir sind auf der **ProWein Düsseldorf** vertreten und freuen uns auf ein persönliches Gespräch.\n\nMit freundlichen Grüßen,\n**Marco Sechi**\nExportleiter, Tenute Ichnos\nJerzu, Ogliastra — Sardinien, Italien",
            "cta_text": "Jetzt Verkostungsmuster anfordern",
        }


# ---------------------------------------------------------------------------
# POST /api/sentiment
# ---------------------------------------------------------------------------
@app.post("/api/sentiment")
def analyze_sentiment(req: SentimentRequest):
    wine = get_wine_or_404(req.wine_id)
    reviews = get_reviews(req.wine_id)

    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found for this wine")

    if gemini_available:
        try:
            result = _sentiment_with_gemini(wine, reviews)
            return JSONResponse({"source": "gemini", "wine_id": req.wine_id, "data": result})
        except Exception as e:
            print(f"[WARN] Gemini sentiment failed: {e}")

    result = _sentiment_mock(wine, reviews)
    return JSONResponse({"source": "mock", "wine_id": req.wine_id, "data": result})


def _sentiment_with_gemini(wine: dict, reviews: list) -> dict:
    reviews_text = "\n\n".join(
        [
            f"[{r['flag']} {r['country'].upper()} | {r['rating']}/5 | {r['author']}]: {r['text']}"
            for r in reviews
        ]
    )

    prompt = f"""You are a senior wine market analyst specializing in semantic review analysis for Italian winery exporters.

WINE: {wine['full_name']}, {wine['vintage']}
WINERY: Tenute Ichnos, Jerzu, Sardinia

REVIEWS TO ANALYZE:
{reviews_text}

TASK: Perform a deep semantic analysis of these reviews. Extract actionable intelligence for the winery's production, marketing, and export strategy.

Focus on:
1. POSITIVE THEMES: What do buyers across markets consistently praise? (group similar praise)
2. NEGATIVE THEMES: What recurring criticisms or suggestions appear? (even mild ones — they signal opportunities)
3. PRODUCTION INSIGHTS: What specific changes to vinification, packaging, or communication does the review data suggest? Be specific and actionable.
4. MARKET SPLIT: How does sentiment differ between USA, Germany, and Italy reviewers?
5. TOP KEYWORDS: Most frequently mentioned meaningful words/concepts

CRITICAL: Return ONLY a valid JSON object with these exact keys:
{{
  "overall_score": number (0-10, weighted average considering all markets),
  "positive_themes": [
    {{"theme": "string", "count": number, "quote": "best representative quote"}}
  ],
  "negative_themes": [
    {{"theme": "string", "count": number, "quote": "best representative quote"}}
  ],
  "production_insights": [
    {{"insight": "string (what the data shows)", "priority": "alta|media|bassa", "action": "string (specific recommended action)"}}
  ],
  "market_split": {{
    "usa_score": number (0-10),
    "germany_score": number (0-10),
    "italy_score": number (0-10)
  }},
  "top_keywords": ["string", "string", "string", "string", "string", "string", "string", "string"]
}}
"""

    raw = call_gemini(prompt)
    return extract_json_from_response(raw)


def _sentiment_mock(wine: dict, reviews: list) -> dict:
    if wine["id"] == "cannonau_riserva":
        return {
            "overall_score": 8.7,
            "positive_themes": [
                {
                    "theme": "Qualità e complessità aromatica eccezionale",
                    "count": 6,
                    "quote": "Absolutely stunning Cannonau… The wine has this incredible depth — dark berries, leather, a hint of Mediterranean herbs.",
                },
                {
                    "theme": "Eccellente rapporto qualità-prezzo vs. competitor internazionali",
                    "count": 5,
                    "quote": "At this price point it absolutely destroys many Napa Cabs I pay twice as much for.",
                },
                {
                    "theme": "Struttura tannica superiore e potenziale di invecchiamento",
                    "count": 4,
                    "quote": "Lagerpotenzial schätze ich auf 10–12 Jahre problemlos.",
                },
                {
                    "theme": "Abbinamenti gastronomici premium (carni rosse, agnello)",
                    "count": 4,
                    "quote": "I paired this with a dry-aged ribeye at our neighborhood steakhouse and it was a revelation.",
                },
            ],
            "negative_themes": [
                {
                    "theme": "Eccessiva influenza del legno (barrique troppo presente)",
                    "count": 3,
                    "quote": "The oak is slightly too dominant for my taste — it somewhat muffles the terroir character.",
                },
                {
                    "theme": "Assenza di schede tecniche in inglese/tedesco sull'etichetta",
                    "count": 3,
                    "quote": "Datenblatt auf Englisch wäre wünschenswert für die professionelle Einschätzung.",
                },
                {
                    "theme": "Design dell'etichetta datato, inadeguato per mercati export",
                    "count": 2,
                    "quote": "Das Etikett wirkt leider etwas veraltet — hier könnte die Tenute Ichnos modernisieren.",
                },
            ],
            "production_insights": [
                {
                    "insight": "3 recensori su 8 segnalano l'eccesso di barrique come difetto principale. La percentuale di legno nuovo (30%) copre la mineralità del granito ogliastrese che è il principale differenziatore del vino.",
                    "priority": "alta",
                    "action": "Ridurre percentuale barrique nuovo al 15-20% nel prossimo ciclo di affinamento. Valutare inserimento di botti grandi da 25 hl per 6 mesi a completamento del ciclo.",
                },
                {
                    "insight": "Mercato USA e DE chiedono entrambi informazioni tecniche in lingua nella comunicazione (etichetta, tech sheet). Questo ostacola l'acquisto professionale e il riordino.",
                    "priority": "alta",
                    "action": "Produrre tech sheet PDF bilingue (EN/DE) con QR code sull'etichetta posteriore. Aggiornare retroetichetta con tasting notes in inglese.",
                },
                {
                    "insight": "Il design dell'etichetta è percepito come datato in Germania (2 menzioni esplicite). L'estetica influisce sulla shelf appeal in Weinhandlungen e wine shop premium.",
                    "priority": "media",
                    "action": "Investire in un restyling dell'etichetta con designer specializzato in wine branding per mercati nordeuropei. Mantenere l'heritage ma modernizzare la leggibilità.",
                },
                {
                    "insight": "Il collegamento con la Blue Zone dell'Ogliastra genera entusiasmo organico nei recensori USA ('incredible backstory'). Non è ancora sfruttato nelle comunicazioni ufficiali.",
                    "priority": "media",
                    "action": "Inserire il claim 'From Sardinia's Blue Zone — One of Earth's 5 Longevity Regions' su tutti i materiali di comunicazione per il mercato USA.",
                },
            ],
            "market_split": {"usa_score": 8.4, "germany_score": 8.9, "italy_score": 9.1},
            "top_keywords": [
                "tannini setosi",
                "mineralità",
                "barrique",
                "Blue Zone",
                "longevità",
                "abbinamento carni",
                "potenziale invecchiamento",
                "terroir granico",
            ],
        }
    elif wine["id"] == "vermentino_docg":
        return {
            "overall_score": 8.5,
            "positive_themes": [
                {
                    "theme": "Profilo aromatico eccezionale e mineralità salmastra unica",
                    "count": 5,
                    "quote": "The aroma alone — citrus, white flowers, wild herbs — transports you to the Mediterranean coast.",
                },
                {
                    "theme": "Perfetto per abbinamenti con pesce e crudi di mare",
                    "count": 4,
                    "quote": "Paired it with grilled shrimp and a light ceviche at our summer cookout and it was perfect.",
                },
                {
                    "theme": "Qualità DOCG percepita come garanzia di eccellenza tecnica",
                    "count": 3,
                    "quote": "Bemerkenswerte DOCG-Qualität.",
                },
            ],
            "negative_themes": [
                {
                    "theme": "Palato meno complesso dell'aspetto olfattivo promesso",
                    "count": 2,
                    "quote": "I found it slightly simple on the palate compared to the nose, which promises more than it delivers.",
                },
                {
                    "theme": "Design etichetta poco moderno per mercato USA",
                    "count": 2,
                    "quote": "Label looks a bit old-fashioned for the American market — a more modern design could help shelf appeal.",
                },
                {
                    "theme": "Assenza di informazioni in inglese sull'etichetta",
                    "count": 1,
                    "quote": "Could use tasting notes in English directly on the bottle.",
                },
            ],
            "production_insights": [
                {
                    "insight": "Il gap tra naso promettente e palato percepito come 'semplice' suggerisce che la texture potrebbe essere migliorata senza perdere freschezza.",
                    "priority": "media",
                    "action": "Estendere il contatto sui lieviti fini da 4 a 6 mesi con bâtonnage più frequente per aumentare la complessità palatale e la sensazione di corpo.",
                },
                {
                    "insight": "L'etichetta è menzionata come ostacolo alla shelf appeal in USA da 2 recensori indipendenti.",
                    "priority": "alta",
                    "action": "Sviluppare una versione USA-specifica dell'etichetta con design contemporaneo e informazioni in inglese. Mantenere la versione italiana per il mercato domestico.",
                },
            ],
            "market_split": {"usa_score": 8.1, "germany_score": 9.0, "italy_score": 9.2},
            "top_keywords": [
                "mineralità",
                "DOCG",
                "agrumi",
                "salinità",
                "sur lies",
                "notte",
                "freschezza",
                "seafood",
            ],
        }
    else:
        return {
            "overall_score": 8.8,
            "positive_themes": [
                {
                    "theme": "Eleganza e bevibilità sorprendenti per il vitigno Carignano",
                    "count": 5,
                    "quote": "Eleganz und Trinkfreude, die Liebhaber von Burgund und Norditalien ansprechen wird.",
                },
                {
                    "theme": "Rarità e unicità: Carignano è sconosciuto in Germania",
                    "count": 4,
                    "quote": "Das Carignano del Sulcis ist in Deutschland praktisch unbekannt, was ein Jammer ist.",
                },
                {
                    "theme": "Rapporto qualità-prezzo eccezionale vs. analoghe denominazioni italiane",
                    "count": 3,
                    "quote": "Se fosse toscano costerebbe il doppio.",
                },
                {
                    "theme": "Rebe anziane Alberello conferiscono concentrazione e freschezza simultanee",
                    "count": 4,
                    "quote": "60-jährige Alberello-Reben liefern eine Konzentration und Eleganz, die ihresgleichen sucht.",
                },
            ],
            "negative_themes": [
                {
                    "theme": "Distribuzione sporadica in Germania, difficile da reperire",
                    "count": 2,
                    "quote": "Der Vertrieb in Deutschland ist noch sehr sporadisch.",
                },
                {
                    "theme": "Inconsistenza tra annate percepita da collezionisti",
                    "count": 1,
                    "quote": "Was mich leicht stört ist die fehlende Konsistenz im Jahrgangsvergleich.",
                },
                {
                    "theme": "Assenza di tech sheet professionale in inglese/tedesco",
                    "count": 2,
                    "quote": "Für professionelle Einkäufer würde ich mir detailliertere technische Datenblätter auf Englisch oder Deutsch wünschen.",
                },
            ],
            "production_insights": [
                {
                    "insight": "La distribuzione in Germania è il principale bottleneck: 2 recensori lo segnalano esplicitamente. Il vino ha ottimi fondamentali ma non arriva agli acquirenti giusti.",
                    "priority": "alta",
                    "action": "Prioritizzare accordo con importatore tedesco specializzato in vini biodinamici e da vigne vecchie. Target: Weinhandlungen Hamburg, Monaco, Berlino.",
                },
                {
                    "insight": "I collezionisti tedeschi notano inconsistenza tra annate (2018 vs 2020). Può essere dovuta a variabilità vendemmia su viti anziane o differenze di protocollo.",
                    "priority": "media",
                    "action": "Implementare protocollo di selezione parcelle fisso per le bottiglie DOC, con documentazione dell'annata per comunicazione importatori.",
                },
                {
                    "insight": "Tech sheet professionale in DE/EN è richiesto esplicitamente da professionisti. Assenza di questo documento è un barrier to purchase per buyer tedeschi.",
                    "priority": "alta",
                    "action": "Produrre tech sheet a 4 pagine in EN e DE con: dati viticoli, analisi chimiche, finestra di consumo, suggerimenti di abbinamento. Disponibile su sito e QR etichetta.",
                },
            ],
            "market_split": {"usa_score": 0.0, "germany_score": 8.8, "italy_score": 8.9},
            "top_keywords": [
                "Alberello",
                "60 anni",
                "eleganza",
                "Carignano",
                "Sulcis",
                "Burgund",
                "distribuzione",
                "rarità",
            ],
        }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=True)
