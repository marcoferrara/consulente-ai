# computer_use.py
# Loop Claude API con Computer Use per navigare il software EPC sul desktop remoto.
# Claude vede screenshot → decide l'azione → RDPController la esegue → repeat.

import os
import io
import base64
import logging
import time
from typing import Optional
from PIL import Image
import anthropic

from agent.rdp_controller import RDPController

logger = logging.getLogger(__name__)

# Modello Claude con le migliori capacità di computer use
MODELLO = "claude-opus-4-8"

# Numero massimo di iterazioni per evitare loop infiniti
MAX_ITERAZIONI = 40

# Dimensione massima screenshot inviato a Claude (riduce costi token)
MAX_SCREENSHOT_W = 1280
MAX_SCREENSHOT_H = 800


class ComputerUseAgent:
    """
    Agente Claude con Computer Use.
    Riceve screenshots dal RDPController e comanda le azioni da eseguire.
    """

    def __init__(self, rdp: RDPController):
        self.rdp = rdp
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self._messages: list[dict] = []

    def _screenshot_a_base64(self, img: Image.Image) -> str:
        """Ridimensiona (se necessario) e converte l'immagine in base64 PNG."""
        # Ridimensiona per ridurre costi e tempi di upload
        if img.width > MAX_SCREENSHOT_W or img.height > MAX_SCREENSHOT_H:
            img.thumbnail((MAX_SCREENSHOT_W, MAX_SCREENSHOT_H), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.standard_b64encode(buf.getvalue()).decode("utf-8")

    def _screenshot_corrente(self) -> dict:
        """Cattura lo screenshot corrente e lo restituisce come blocco content per Claude."""
        img = self.rdp.cattura_screenshot()
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": self._screenshot_a_base64(img),
            },
        }

    def _build_system_prompt(
        self,
        marchio: str,
        kb_testo: str,
        ricambi: list[str],
        telaio: str,
    ) -> str:
        """
        Costruisce il system prompt per Claude includendo la knowledge base del marchio
        e la lista dei ricambi da cercare.
        """
        ricambi_formattati = "\n".join(f"  - {r}" for r in ricambi)

        return f"""Sei un operatore esperto di ricambi per camion italiani che naviga il software EPC del marchio {marchio}.

Il tuo obiettivo è trovare TUTTI i codici originali per ogni ricambio nell'elenco seguente, per il telaio specificato.

TELAIO: {telaio}
MARCHIO: {marchio}

RICAMBI DA CERCARE:
{ricambi_formattati}

GUIDA OPERATIVA PER {marchio}:
{kb_testo}

ISTRUZIONI OPERATIVE:
1. Naviga il software EPC seguendo la guida operativa sopra.
2. Per ogni ricambio nell'elenco:
   a. Naviga alla sezione corretta del catalogo
   b. Identifica il particolare
   c. Annota TUTTI i codici originali (incluse sostituzioni storiche — la catena completa)
   d. Identifica le coordinate (x, y) del particolare nella tavola esplosa per lo screenshot
3. Quando hai trovato tutti i codici per tutti i ricambi, restituisci un JSON strutturato
   con la chiave "completato": true e i risultati.
4. Se non riesci a trovare un particolare dopo vari tentativi, annotalo come "non trovato"
   e passa al successivo.
5. Se il programma mostra un errore o una schermata inaspettata, prova a chiuderlo e riaprirlo.

FORMATO RISPOSTA FINALE (quando hai completato):
Quando hai trovato tutto, nella tua risposta finale includi un blocco JSON:
```json
{{
  "completato": true,
  "risultati": [
    {{
      "ricambio": "nome ricambio",
      "trovato": true,
      "codici": [
        {{"codice": "12345678", "stato": "attuale"}},
        {{"codice": "87654321", "stato": "sostituito_da_12345678"}}
      ],
      "screenshot_coordinate": {{"x": 640, "y": 400}},
      "note": "eventuale nota"
    }}
  ]
}}
```

IMPORTANTE:
- Agisci con precisione, un'azione alla volta.
- Se qualcosa non è chiaro nello screenshot, scatta un nuovo screenshot prima di agire.
- Non digitare mai dati personali o credenziali — usa solo il telaio fornito.
- Se dopo {MAX_ITERAZIONI} azioni non hai completato, restituisci i risultati parziali con "completato": true.
"""

    async def esegui_ricerca(
        self,
        marchio: str,
        kb_testo: str,
        ricambi: list[str],
        telaio: str,
    ) -> list[dict]:
        """
        Esegue il loop principale di computer use.
        Restituisce la lista dei risultati per ogni ricambio.
        """
        system = self._build_system_prompt(marchio, kb_testo, ricambi, telaio)

        # Messaggio iniziale con lo screenshot corrente
        screenshot_iniziale = self._screenshot_corrente()
        self._messages = [
            {
                "role": "user",
                "content": [
                    screenshot_iniziale,
                    {"type": "text", "text": "Questo è lo stato attuale del desktop remoto. Inizia la ricerca seguendo le istruzioni."},
                ],
            }
        ]

        # Definizione degli strumenti computer use disponibili
        tools = [
            {
                "type": "computer_20250124",
                "name": "computer",
                "display_width_px": MAX_SCREENSHOT_W,
                "display_height_px": MAX_SCREENSHOT_H,
            }
        ]

        risultati: list[dict] = []

        for iterazione in range(MAX_ITERAZIONI):
            logger.info(f"Iterazione computer use {iterazione + 1}/{MAX_ITERAZIONI}")

            risposta = self.client.messages.create(
                model=MODELLO,
                max_tokens=4096,
                system=system,
                tools=tools,
                messages=self._messages,
            )

            # Aggiunge la risposta di Claude alla cronologia
            self._messages.append({"role": "assistant", "content": risposta.content})

            # Controlla se Claude ha completato il task (stop_reason = "end_turn")
            if risposta.stop_reason == "end_turn":
                # Cerca il JSON dei risultati nel testo della risposta
                risultati = self._estrai_risultati(risposta.content)
                logger.info(f"Ricerca completata dopo {iterazione + 1} iterazioni")
                break

            # Gestisce le azioni richieste da Claude (tool_use)
            tool_results = []
            for blocco in risposta.content:
                if blocco.type != "tool_use":
                    continue

                if blocco.name == "computer":
                    esito = self._esegui_azione_computer(blocco.input)
                    # Dopo ogni azione, cattura il nuovo screenshot come risultato
                    nuovo_screenshot = self._screenshot_corrente()
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": blocco.id,
                        "content": [nuovo_screenshot],
                    })

            if not tool_results:
                # Nessuna azione → Claude ha finito senza esplicitare "end_turn"
                risultati = self._estrai_risultati(risposta.content)
                break

            # Aggiunge i risultati degli strumenti come prossimo messaggio utente
            self._messages.append({"role": "user", "content": tool_results})

        return risultati

    def _esegui_azione_computer(self, input_azione: dict) -> str:
        """
        Esegue l'azione richiesta da Claude sul RDPController.
        Restituisce una stringa descrittiva dell'azione eseguita.
        """
        azione = input_azione.get("action", "")
        coordinate = input_azione.get("coordinate", [])

        try:
            if azione == "screenshot":
                # Screenshot già catturato come tool_result — niente da fare
                pass

            elif azione == "left_click":
                x, y = coordinate
                self.rdp.clicca(x, y)
                logger.debug(f"Click sinistro su ({x}, {y})")

            elif azione == "double_click":
                x, y = coordinate
                self.rdp.clicca(x, y, doppio=True)
                logger.debug(f"Doppio click su ({x}, {y})")

            elif azione == "right_click":
                import pyautogui
                x, y = coordinate
                self.rdp.porta_in_primo_piano()
                pyautogui.rightClick(x, y)
                logger.debug(f"Click destro su ({x}, {y})")

            elif azione == "type":
                testo = input_azione.get("text", "")
                self.rdp.digita_testo(testo)
                logger.debug(f"Digitato: {testo[:30]}...")

            elif azione == "key":
                tasto = input_azione.get("text", "")
                self.rdp.premi_tasto(tasto)
                logger.debug(f"Tasto: {tasto}")

            elif azione == "scroll":
                x, y = coordinate
                direzione = input_azione.get("direction", "down")
                dir_it = "giu" if direzione == "down" else "su"
                self.rdp.scorri(x, y, dir_it, passi=input_azione.get("amount", 3))

            elif azione == "mouse_move":
                import pyautogui
                x, y = coordinate
                pyautogui.moveTo(x, y)

            else:
                logger.warning(f"Azione computer use non gestita: {azione}")

        except Exception as e:
            logger.error(f"Errore durante l'azione '{azione}': {e}")

        time.sleep(0.5)  # Piccola pausa per stabilità UI
        return f"Azione '{azione}' eseguita"

    def _estrai_risultati(self, content_blocks: list) -> list[dict]:
        """
        Cerca il blocco JSON con i risultati nella risposta testuale di Claude.
        Restituisce lista vuota se non trovato.
        """
        import json
        import re

        testo_completo = " ".join(
            b.text for b in content_blocks
            if hasattr(b, "text")
        )

        # Cerca blocco JSON tra ```json ... ```
        match = re.search(r"```json\s*(\{.*?\})\s*```", testo_completo, re.DOTALL)
        if match:
            try:
                dati = json.loads(match.group(1))
                return dati.get("risultati", [])
            except json.JSONDecodeError as e:
                logger.error(f"Errore parsing JSON risultati: {e}")

        # Fallback: cerca un oggetto JSON grezzo con "completato"
        match2 = re.search(r'\{"completato".*?\}', testo_completo, re.DOTALL)
        if match2:
            try:
                dati = json.loads(match2.group(0))
                return dati.get("risultati", [])
            except json.JSONDecodeError:
                pass

        logger.warning("Nessun JSON risultati trovato nella risposta di Claude")
        return []
