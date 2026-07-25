# orchestrator.py
# Coordinatore principale: gestisce l'intero flusso di una ricerca ricambi

import os
import time
import logging
import yaml
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image

from agent.vin_decoder import decode_vin
from agent.rdp_controller import RDPController
from agent.computer_use import ComputerUseAgent
from agent.image_annotator import salva_screenshot_annotato
from agent.notifier import formatta_messaggio, invia_whatsapp, invia_screenshot_whatsapp

logger = logging.getLogger(__name__)

# Percorso cartella knowledge base relativo a questo file
KB_DIR = Path(__file__).parent.parent / "knowledge_base"

# Cartella dove salvare gli screenshot annotati
SCREENSHOTS_DIR = Path(__file__).parent.parent / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)


def carica_knowledge_base(marchio: str) -> Tuple[dict, str]:
    """
    Carica il file YAML della knowledge base per il marchio indicato.
    Restituisce (dati_yaml, testo_formattato_per_claude).
    Lancia FileNotFoundError se il file non esiste.
    """
    nome_file = f"{marchio.lower()}.yaml"
    percorso = KB_DIR / nome_file

    if not percorso.exists():
        raise FileNotFoundError(f"Knowledge base non trovata per marchio '{marchio}': {percorso}")

    with open(percorso, "r", encoding="utf-8") as f:
        dati = yaml.safe_load(f)

    # Costruisce un testo descrittivo della KB da passare a Claude nel system prompt
    testo = _kb_a_testo(dati)
    return dati, testo


def _kb_a_testo(dati: dict) -> str:
    """
    Converte la knowledge base YAML in testo leggibile da Claude.
    """
    righe = []

    software = dati.get("software_nome", "Software EPC")
    righe.append(f"SOFTWARE: {software}")

    if dati.get("software_icona_desktop"):
        righe.append(f"Icona sul desktop: {dati['software_icona_desktop']}")
    if dati.get("software_url"):
        righe.append(f"URL web: {dati['software_url']}")

    righe.append("")

    # Passi di avvio
    avvio = dati.get("avvio", [])
    if avvio:
        righe.append("AVVIO APPLICAZIONE:")
        for passo in avvio:
            if passo.get("tipo") == "note_contestuale":
                righe.append(f"  → {passo.get('testo', '')}")
            else:
                target = passo.get("target", "")
                note = passo.get("note", "")
                righe.append(f"  [{passo.get('tipo', '').upper()}] {target} — {note}")

    righe.append("")

    # Inserimento telaio
    ins = dati.get("inserimento_telaio", [])
    if ins:
        righe.append("INSERIMENTO TELAIO:")
        for passo in ins:
            if passo.get("tipo") == "note_contestuale":
                righe.append(f"  → {passo.get('testo', '')}")
            else:
                righe.append(f"  [{passo.get('tipo', '').upper()}] {passo.get('campo', passo.get('target', ''))} — {passo.get('note', '')}")

    righe.append("")

    # Particolarità
    particolarita = dati.get("particolarita", [])
    if particolarita:
        righe.append("PARTICOLARITÀ E NOTE IMPORTANTI:")
        for p in particolarita:
            if isinstance(p, dict):
                modelli = p.get("modelli", [])
                nota = p.get("note", "")
                if modelli:
                    righe.append(f"  [{', '.join(modelli)}] {nota}")
                else:
                    righe.append(f"  → {nota}")
            else:
                righe.append(f"  → {p}")

    righe.append("")

    # Codici di sostituzione
    codici_sub = dati.get("codici_sostituzione", [])
    if codici_sub:
        righe.append("GESTIONE CODICI DI SOSTITUZIONE:")
        for c in codici_sub:
            testo = c.get("testo", c) if isinstance(c, dict) else c
            righe.append(f"  → {testo}")

    righe.append("")

    # Categorie / percorsi
    categorie = dati.get("categorie", {})
    if categorie:
        righe.append("PERCORSI NEL CATALOGO (per categoria):")
        for nome_cat, info in categorie.items():
            if isinstance(info, dict):
                percorso = info.get("percorso", "")
                sinonimi = ", ".join(info.get("sinonimi", []))
                righe.append(f"  {percorso}")
                if sinonimi:
                    righe.append(f"    Sinonimi: {sinonimi}")

    return "\n".join(righe)


class OrchestratoreRicerca:
    """
    Coordina l'intero processo di ricerca:
    1. Decodifica il marchio dal telaio
    2. Carica la knowledge base
    3. Apre la sessione RDP
    4. Esegue la ricerca con l'agente computer use
    5. Annota gli screenshot
    6. Invia il report via WhatsApp
    """

    async def esegui(
        self,
        telaio: str,
        ricambi: list[str],
        marchio: Optional[str] = None,
        cliente: Optional[str] = None,
    ) -> Tuple[list[dict], str]:
        """
        Esegue la ricerca completa.
        Restituisce (lista_risultati, messaggio_formattato).
        """
        inizio = time.time()

        # 1. Decodifica marchio se non passato esplicitamente
        if not marchio:
            marchio = decode_vin(telaio)
            if not marchio:
                raise ValueError(f"Marchio non riconosciuto per telaio: {telaio}")

        logger.info(f"Avvio ricerca — Marchio: {marchio} — Telaio: {telaio} — Ricambi: {ricambi}")

        # 2. Carica knowledge base
        try:
            kb_dati, kb_testo = carica_knowledge_base(marchio)
        except FileNotFoundError as e:
            logger.error(str(e))
            raise

        # 3. Apri sessione RDP ed esegui ricerca con computer use
        risultati: list[dict] = []
        percorsi_screenshot: list[str] = []

        with RDPController() as rdp:
            agente = ComputerUseAgent(rdp)
            risultati = await agente.esegui_ricerca(
                marchio=marchio,
                kb_testo=kb_testo,
                ricambi=ricambi,
                telaio=telaio,
            )

            # 4. Cattura e annota screenshot per ogni risultato trovato
            for i, r in enumerate(risultati):
                if not r.get("trovato"):
                    continue

                coord = r.get("screenshot_coordinate")
                if not coord:
                    continue

                try:
                    img = rdp.cattura_screenshot()
                    nome_file = SCREENSHOTS_DIR / f"{telaio}_{i+1}_{r.get('ricambio','articolo').replace(' ', '_')[:30]}.png"
                    percorso = salva_screenshot_annotato(
                        img,
                        x=coord.get("x", 640),
                        y=coord.get("y", 400),
                        nome_file=str(nome_file),
                    )
                    r["screenshot_path"] = percorso
                    percorsi_screenshot.append(percorso)
                    logger.info(f"Screenshot annotato salvato: {percorso}")
                except Exception as e:
                    logger.warning(f"Impossibile catturare screenshot per '{r.get('ricambio')}': {e}")

        # 5. Componi e invia il messaggio
        tempo_totale = time.time() - inizio
        messaggio = formatta_messaggio(
            telaio=telaio,
            marchio=marchio,
            risultati=risultati,
            cliente=cliente,
            tempo_secondi=tempo_totale,
        )

        logger.info(f"Ricerca completata in {tempo_totale:.0f}s — {len(risultati)} ricambi elaborati")

        # Invio WhatsApp testo
        await invia_whatsapp(messaggio)

        # Invio screenshot (se il gateway supporta immagini)
        for percorso in percorsi_screenshot:
            await invia_screenshot_whatsapp(percorso)

        return risultati, messaggio
