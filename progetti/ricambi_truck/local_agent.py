#!/usr/bin/env python3
import os
import sys
import time
import argparse
import yaml
import logging
from PIL import Image, ImageDraw, ImageFont
import mss
import ollama
import json
import re

# Configurazione Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class MockPyAutoGUI:
    FAILSAFE = True
    PAUSE = 0.5
    class FailSafeException(Exception):
        pass
    @staticmethod
    def size():
        return (1920, 1080)
    @staticmethod
    def moveTo(x, y, duration=0):
        pass
    @staticmethod
    def click():
        pass
    @staticmethod
    def doubleClick():
        pass
    @staticmethod
    def write(text, interval=0):
        pass
    @staticmethod
    def press(key):
        pass

try:
    import pyautogui
except ImportError:
    logger.warning("ATTENZIONE: pyautogui non è installato o non può essere caricato su questo sistema. Le funzioni di interazione fisica (click, tastiera) non saranno disponibili in modalità reale, ma funzionerà il --dry-run.")
    pyautogui = MockPyAutoGUI

# Impostazioni di sicurezza se pyautogui reale è presente
if not isinstance(pyautogui, type) or pyautogui != MockPyAutoGUI:
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.5



class LocalEPCAgent:
    def __init__(self, brand: str, variables: dict, model_name: str = "qwen2.5vl", connect: bool = False):
        self.brand = brand.lower()
        self.variables = variables
        self.model_name = model_name
        self.connect = connect
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.yaml_path = os.path.join(self.base_dir, "istruzioni", f"{self.brand}.yaml")
        self.connection_yaml_path = os.path.join(self.base_dir, "istruzioni", "connessione.yaml")
        self.instructions = {}
        self.connection_instructions = {}
        
        # Carica istruzioni
        self._load_yaml()
        if self.connect:
            self._load_connection_yaml()

    def _load_yaml(self):
        if not os.path.exists(self.yaml_path):
            raise FileNotFoundError(f"File di istruzioni non trovato: {self.yaml_path}")
        with open(self.yaml_path, "r", encoding="utf-8") as f:
            self.instructions = yaml.safe_load(f)
        logger.info(f"Istruzioni per {self.brand.upper()} caricate correttamente.")

    def _load_connection_yaml(self):
        if not os.path.exists(self.connection_yaml_path):
            logger.warning(f"File di connessione non trovato: {self.connection_yaml_path}. Salto la fase di connessione.")
            self.connect = False
            return
        with open(self.connection_yaml_path, "r", encoding="utf-8") as f:
            self.connection_instructions = yaml.safe_load(f)
        logger.info("Istruzioni per la connessione al Desktop Remoto caricate con successo.")

    def _replace_placeholders(self, text: str) -> str:
        """Sostituisce i placeholder come {{TELAIO}} o {{RICAMBIO}} con i valori reali."""
        if not isinstance(text, str):
            return text
        for key, val in self.variables.items():
            text = text.replace(f"{{{{{key.upper()}}}}}", str(val))
        return text

    def capture_screen_with_grid(self, grid_cols=20, grid_rows=15) -> tuple:
        """
        Cattura lo schermo intero e disegna una griglia visiva sopra di esso.
        Ritorna il percorso dell'immagine con griglia salvata e le informazioni di scaling.
        """
        # Ottieni dimensioni logiche dello schermo
        logical_w, logical_h = pyautogui.size()
        
        # Cattura lo schermo usando mss (molto veloce)
        with mss.mss() as sct:
            # Cattura monitor principale (monitor 1)
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
        captured_w, captured_h = img.size
        scale_x = captured_w / logical_w
        scale_y = captured_h / logical_h
        
        logger.info(f"Schermo catturato: logico {logical_w}x{logical_h}, catturato {captured_w}x{captured_h} (Scale X: {scale_x}, Y: {scale_y})")

        # Disegna la griglia sull'immagine catturata
        draw = ImageDraw.Draw(img)
        
        # Dimensione delle celle della griglia
        cell_w = captured_w / grid_cols
        cell_h = captured_h / grid_rows
        
        # Prova a caricare un font predefinito leggibile, altrimenti usa quello di default
        try:
            # Sui sistemi moderni proviamo a cercare un font sans-serif
            font = ImageFont.load_default()
        except:
            font = None

        # Disegna linee e etichette
        for col in range(grid_cols):
            # Linee verticali
            x = int(col * cell_w)
            draw.line([(x, 0), (x, captured_h)], fill=(255, 0, 0, 128), width=1)
            
            # Etichetta colonna (A, B, C...)
            col_label = chr(65 + col) if col < 26 else f"A{chr(65 + col - 26)}"
            
            for row in range(grid_rows):
                # Linee orizzontali
                if col == 0:
                    y = int(row * cell_h)
                    draw.line([(0, y), (captured_w, y)], fill=(255, 0, 0, 128), width=1)
                
                # Etichetta cella (es. A1, B5)
                y = int(row * cell_h)
                cell_name = f"{col_label}{row + 1}"
                
                # Sfondo nero per l'etichetta per renderla leggibile
                text_pos = (x + 3, y + 3)
                draw.rectangle([text_pos, (text_pos[0] + 28, text_pos[1] + 13)], fill=(0, 0, 0))
                draw.text(text_pos, cell_name, fill=(255, 255, 255), font=font)

        # Salva l'immagine temporanea
        temp_dir = os.path.join(self.base_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        grid_img_path = os.path.join(temp_dir, "screenshot_grid.png")
        img.save(grid_img_path)
        
        return grid_img_path, scale_x, scale_y, cell_w, cell_h

    def ask_ollama_for_target(self, grid_img_path: str, target_desc: str) -> str:
        """
        Invia lo screenshot grigliato ad Ollama chiedendo la cella contenente l'obiettivo.
        """
        logger.info(f"Chiedo a Ollama ({self.model_name}) di individuare: '{target_desc}'")
        
        prompt = f"""
Sei un agente robotico che controlla un computer. Guarda questo screenshot dello schermo su cui è sovrapposta una griglia rossa.
Ogni cella della griglia è contrassegnata da una coordinata (es. A1, B3, C10, ecc.).

Il tuo compito è trovare ed identificare l'elemento descritto come: "{target_desc}".

Rispondi fornendo la coordinata esatta della cella che contiene il centro dell'elemento descritto (es. "C4").
Rispondi in formato JSON con la chiave "cell", per esempio:
{{"cell": "C4"}}

Non aggiungere spiegazioni, fornisci SOLO il JSON richiesto.
"""
        
        try:
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                images=[grid_img_path],
                options={"temperature": 0.0} # Bassa temperatura per massima precisione deterministica
            )
            
            result_text = response.get("response", "").strip()
            logger.info(f"Risposta grezza Ollama: {result_text}")
            
            # Estrae il codice cella usando regex
            match = re.search(r'"cell"\s*:\s*"([A-Z0-9]+)"', result_text, re.IGNORECASE)
            if not match:
                # Prova a cercare una coordinata semplice se il JSON non è perfetto
                match = re.search(r'\b([A-Z]{1,2}\d{1,2})\b', result_text)
                
            if match:
                cell = match.group(1).upper()
                logger.info(f"Cella individuata con successo: {cell}")
                return cell
            else:
                logger.warning("Impossibile fare il parsing della coordinata dalla risposta di Ollama.")
                return None
        except Exception as e:
            logger.error(f"Errore nella chiamata a Ollama: {e}")
            return None

    def execute_gui_action(self, action: dict, scale_x: float, scale_y: float, cell_w: float, cell_h: float):
        """Esegue un'azione PyAutoGUI basata sulla coordinata della cella identificata."""
        action_type = action.get("tipo")
        target_desc = self._replace_placeholders(action.get("target", ""))
        note = action.get("note", "")

        logger.info(f"Azione: {action_type.upper()} su '{target_desc}' | Note: {note}")

        if action_type in ["click", "doppio_click"]:
            # 1. Cattura e invia a Ollama
            grid_img_path, cur_scale_x, cur_scale_y, cur_cell_w, cur_cell_h = self.capture_screen_with_grid()
            cell = self.ask_ollama_for_target(grid_img_path, target_desc)
            
            if not cell:
                logger.error(f"Impossibile determinare la posizione per '{target_desc}'. Salto l'azione.")
                return

            # Calcola colonna e riga dalla cella (es: "B5" o "AC12")
            match = re.match(r'^([A-Z]+)(\d+)$', cell)
            if not match:
                logger.error(f"Formato cella non valido: {cell}")
                return
                
            col_str, row_str = match.groups()
            
            # Converti lettera in colonna index (A=0, B=1, ..., Z=25, AA=26)
            col_idx = 0
            for char in col_str:
                col_idx = col_idx * 26 + (ord(char) - 64)
            col_idx -= 1 # 0-indexed
            
            row_idx = int(row_str) - 1 # 0-indexed
            
            # Centro della cella nei pixel dell'immagine catturata
            center_x_captured = (col_idx * cur_cell_w) + (cur_cell_w / 2)
            center_y_captured = (row_idx * cur_cell_h) + (cur_cell_h / 2)
            
            # Converti in coordinate logiche per PyAutoGUI
            target_x = int(center_x_captured / cur_scale_x)
            target_y = int(center_y_captured / cur_scale_y)
            
            logger.info(f"Muovo il mouse su cella {cell} -> coordinate logiche pixel: X={target_x}, Y={target_y}")
            
            # Sposta gradualmente il mouse (effetto umano per sicurezza)
            pyautogui.moveTo(target_x, target_y, duration=0.8)
            
            if action_type == "click":
                pyautogui.click()
            elif action_type == "doppio_click":
                pyautogui.doubleClick()
                
        elif action_type == "input_testo":
            valore = self._replace_placeholders(action.get("valore", ""))
            logger.info(f"Digito il testo: '{valore}'")
            # Clicca sul campo prima di scrivere per sicurezza (usando l'ultimo target se disponibile)
            pyautogui.write(valore, interval=0.05)
            
        elif action_type == "invio":
            logger.info("Invio tasto ENTER")
            pyautogui.press("enter")
            
        elif action_type == "attendi":
            secondi = action.get("secondi", 2)
            logger.info(f"Attesa di {secondi} secondi...")
            time.sleep(secondi)
            
        elif action_type == "note_contestuale":
            # Questa è solo una nota informativa per l'operatore/log, nessuna azione fisica
            logger.info(f"[Nota Contestuale]: {self._replace_placeholders(action.get('testo', ''))}")

    def run(self, dry_run=False):
        """Esegue sequenzialmente tutte le fasi del file YAML."""
        try:
            # Fase 0: Connessione Desktop Remoto (opzionale)
            if self.connect and self.connection_instructions:
                logger.info(f"=== INIZIO FASE: CONNESSIONE DESKTOP REMOTO ({self.connection_instructions.get('software_nome', 'AnyDesk')}) ===")
                fasi_conn = ["avvio"]
                for fase in fasi_conn:
                    if fase in self.connection_instructions:
                        azioni = self.connection_instructions[fase]
                        for azione in azioni:
                            if dry_run:
                                action_type = azione.get("tipo")
                                target = self._replace_placeholders(azione.get("target", azione.get("testo", azione.get("valore", ""))))
                                logger.info(f"[DRY-RUN] Avrei eseguito (Connessione): {action_type.upper()} -> {target}")
                            else:
                                self.execute_gui_action(azione, 1, 1, 1, 1)
                logger.info("=== FINE FASE: CONNESSIONE DESKTOP REMOTO ===")

            logger.info(f"Inizio esecuzione automazione per {self.brand.upper()} (Dry-run: {dry_run})")
            
            # Estraiamo le sezioni principali nell'ordine corretto
            fasi = ["avvio", "inserimento_telaio", "navigazione_catalogo"]
            
            for fase in fasi:
                if fase not in self.instructions:
                    logger.warning(f"Fase '{fase}' non definita nel file YAML.")
                    continue
                    
                logger.info(f"=== INIZIO FASE: {fase.upper()} ===")
                azioni = self.instructions[fase]
                
                for azione in azioni:
                    # In dry-run stampiamo solo le azioni senza eseguirle
                    if dry_run:
                        action_type = azione.get("tipo")
                        target = self._replace_placeholders(azione.get("target", azione.get("testo", azione.get("valore", ""))))
                        logger.info(f"[DRY-RUN] Avrei eseguito: {action_type.upper()} -> {target}")
                    else:
                        self.execute_gui_action(azione, 1, 1, 1, 1)
                        
                logger.info(f"=== FINE FASE: {fase.upper()} ===")
                
            logger.info("Automazione completata con successo!")
            
        except pyautogui.FailSafeException:
            logger.error("!!! INTERRUZIONE DI EMERGENZA (FAIL-SAFE) DETECTATA !!! Il mouse è stato spostato in un angolo.")
        except Exception as e:
            logger.error(f"Errore durante l'esecuzione dell'automazione: {e}", exc_info=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agente Vision Desktop per Ricambi Truck")
    parser.add_argument("--brand", required=True, help="Marca del camion (es. iveco, scania, daf)")
    parser.add_argument("--vin", required=True, help="Numero di telaio / targa da cercare")
    parser.add_argument("--part", required=True, help="Nome del ricambio richiesto")
    parser.add_argument("--model", default="qwen2.5vl", help="Nome del modello Vision in Ollama (default: qwen2.5vl)")
    parser.add_argument("--connect", action="store_true", help="Avvia prima il desktop remoto caricando connessione.yaml")
    parser.add_argument("--dry-run", action="store_true", help="Simula l'esecuzione senza muovere il mouse o chiamare Ollama")
    
    args = parser.parse_args()
    
    variables = {
        "telaio": args.vin,
        "targa": args.vin,
        "ricambio": args.part
    }
    
    try:
        agent = LocalEPCAgent(brand=args.brand, variables=variables, model_name=args.model, connect=args.connect)
        agent.run(dry_run=args.dry_run)
    except Exception as e:
        logger.error(f"Errore fatale: {e}")
        sys.exit(1)
