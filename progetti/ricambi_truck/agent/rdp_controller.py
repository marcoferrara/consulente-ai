# rdp_controller.py
# Gestione della sessione RDP: apertura, cattura screenshot, input injection, chiusura

import os
import time
import subprocess
import logging
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageGrab

logger = logging.getLogger(__name__)

# Titolo parziale della finestra RDP da cercare con win32gui
RDP_WINDOW_TITLE_PARTIAL = "Desktop remoto"


class RDPController:
    """
    Controlla una sessione Windows RDP.
    Apre la connessione tramite mstsc.exe, cattura screenshot della finestra
    e inietta input di mouse e tastiera tramite pyautogui.
    """

    def __init__(self):
        self.rdp_host = os.getenv("RDP_HOST")
        self.rdp_user = os.getenv("RDP_USER")
        self.rdp_password = os.getenv("RDP_PASSWORD")
        self.rdp_port = os.getenv("RDP_PORT", "3389")
        self._process: Optional[subprocess.Popen] = None
        self._window_hwnd: Optional[int] = None  # Handle finestra Win32

        # Import pyautogui solo quando necessario (richiede display)
        import pyautogui
        pyautogui.FAILSAFE = True  # Muovi il mouse in alto a sinistra per bloccare
        pyautogui.PAUSE = 0.3      # Pausa tra azioni per stabilità

    def _crea_file_rdp(self) -> str:
        """
        Crea un file .rdp temporaneo con le credenziali di connessione.
        Restituisce il percorso del file creato.
        """
        if not self.rdp_host:
            raise ValueError("RDP_HOST non configurato nel file .env")

        contenuto_rdp = (
            f"full address:s:{self.rdp_host}:{self.rdp_port}\n"
            f"username:s:{self.rdp_user}\n"
            "screen mode id:i:1\n"         # 1 = finestra, 2 = schermo intero
            "desktopwidth:i:1920\n"
            "desktopheight:i:1080\n"
            "session bpp:i:32\n"
            "compression:i:1\n"
            "keyboardhook:i:2\n"
            "audiocapturemode:i:0\n"
            "videoplaybackmode:i:1\n"
            "connection type:i:2\n"
            "networkautodetect:i:1\n"
            "bandwidthautodetect:i:1\n"
            "displayconnectionbar:i:1\n"
            "enableworkspacereconnect:i:0\n"
            "disable wallpaper:i:1\n"      # Disabilita sfondo per performance
            "allow font smoothing:i:0\n"
            "allow desktop composition:i:0\n"
            "disable full window drag:i:1\n"
            "disable menu anims:i:1\n"
            "disable themes:i:0\n"
            "disable cursor setting:i:0\n"
            "bitmapcachepersistenable:i:1\n"
            "redirectprinters:i:0\n"
            "redirectcomports:i:0\n"
            "redirectsmartcards:i:0\n"
            "redirectclipboard:i:1\n"      # Abilita clipboard per incollare telaio
            "redirectposdevices:i:0\n"
            "autoreconnection enabled:i:1\n"
            "authentication level:i:2\n"
            "prompt for credentials:i:0\n"
            "negotiate security layer:i:1\n"
            "remoteapplicationmode:i:0\n"
            "alternate shell:s:\n"
            "shell working directory:s:\n"
            "gatewayhostname:s:\n"
            "gatewayusagemethod:i:4\n"
            "gatewaycredentialssource:i:4\n"
            "gatewayprofileusagemethod:i:0\n"
            "promptcredentialonce:i:0\n"
            "use redirection server name:i:0\n"
            "rdgiskdcproxy:i:0\n"
            "kdcproxyname:s:\n"
        )

        # File temporaneo — verrà cancellato dopo la connessione
        fd, path = tempfile.mkstemp(suffix=".rdp", prefix="truck_rdp_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(contenuto_rdp)

        return path

    def apri_sessione(self, timeout_secondi: int = 30) -> None:
        """
        Apre la sessione RDP tramite mstsc.exe e attende che la finestra sia visibile.
        Lancia ValueError se RDP_HOST non è configurato.
        """
        rdp_file = self._crea_file_rdp()
        logger.info(f"Apertura connessione RDP verso {self.rdp_host}...")

        try:
            # Avvia mstsc con il file .rdp
            self._process = subprocess.Popen(
                ["mstsc.exe", rdp_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Attendi che la finestra RDP appaia
            self._window_hwnd = self._attendi_finestra(timeout_secondi)
            logger.info(f"Sessione RDP aperta. HWND finestra: {self._window_hwnd}")

        finally:
            # Rimuove il file .rdp temporaneo (contiene credenziali in chiaro)
            try:
                os.unlink(rdp_file)
            except Exception:
                pass

    def _attendi_finestra(self, timeout: int) -> int:
        """
        Attende che la finestra RDP appaia sullo schermo e restituisce il suo HWND.
        Solleva TimeoutError se non compare entro il timeout.
        """
        import win32gui

        inizio = time.time()
        while time.time() - inizio < timeout:
            def callback(hwnd, hwnds):
                if win32gui.IsWindowVisible(hwnd):
                    titolo = win32gui.GetWindowText(hwnd)
                    if RDP_WINDOW_TITLE_PARTIAL.lower() in titolo.lower() or \
                       (self.rdp_host and self.rdp_host.lower() in titolo.lower()):
                        hwnds.append(hwnd)

            hwnds: list[int] = []
            win32gui.EnumWindows(callback, hwnds)

            if hwnds:
                return hwnds[0]

            time.sleep(1)

        raise TimeoutError(f"Finestra RDP non trovata entro {timeout} secondi")

    def porta_in_primo_piano(self) -> None:
        """Porta la finestra RDP in primo piano prima di catturare screenshot o iniettare input."""
        if not self._window_hwnd:
            return
        try:
            import win32gui
            import win32con
            win32gui.ShowWindow(self._window_hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(self._window_hwnd)
            time.sleep(0.5)
        except Exception as e:
            logger.warning(f"Impossibile portare la finestra in primo piano: {e}")

    def cattura_screenshot(self) -> Image.Image:
        """
        Cattura uno screenshot dell'intera finestra RDP.
        Restituisce un oggetto PIL.Image pronto per essere inviato a Claude.
        """
        self.porta_in_primo_piano()

        if self._window_hwnd:
            try:
                import win32gui
                rect = win32gui.GetWindowRect(self._window_hwnd)
                # rect = (left, top, right, bottom)
                img = ImageGrab.grab(bbox=rect)
                return img
            except Exception as e:
                logger.warning(f"Screenshot finestra fallito ({e}), cattura schermo intero")

        # Fallback: screenshot dell'intero schermo
        return ImageGrab.grab()

    def clicca(self, x: int, y: int, doppio: bool = False) -> None:
        """
        Clicca alle coordinate (x, y) nella finestra RDP.
        Le coordinate sono relative allo schermo (non alla finestra).
        """
        import pyautogui
        self.porta_in_primo_piano()
        if doppio:
            pyautogui.doubleClick(x, y)
        else:
            pyautogui.click(x, y)
        time.sleep(0.3)

    def digita_testo(self, testo: str, intervallo: float = 0.05) -> None:
        """Digita testo nella finestra RDP attiva."""
        import pyautogui
        self.porta_in_primo_piano()
        pyautogui.typewrite(testo, interval=intervallo)

    def premi_tasto(self, tasto: str) -> None:
        """
        Preme un tasto speciale. Valori comuni: 'enter', 'tab', 'escape',
        'ctrl+a', 'ctrl+c', 'ctrl+v', 'f5', ecc.
        """
        import pyautogui
        self.porta_in_primo_piano()
        if '+' in tasto:
            parti = tasto.split('+')
            pyautogui.hotkey(*parti)
        else:
            pyautogui.press(tasto)
        time.sleep(0.3)

    def incolla_testo(self, testo: str) -> None:
        """
        Copia il testo negli appunti e lo incolla nella finestra RDP.
        Più affidabile di typewrite per stringhe lunghe (es. VIN).
        """
        import pyperclip
        self.porta_in_primo_piano()
        pyperclip.copy(testo)
        time.sleep(0.2)
        self.premi_tasto("ctrl+v")

    def scorri(self, x: int, y: int, direzione: str = "giu", passi: int = 3) -> None:
        """Scrolla in una direzione ('su' o 'giu') nella posizione (x, y)."""
        import pyautogui
        self.porta_in_primo_piano()
        delta = -passi if direzione == "giu" else passi
        pyautogui.scroll(delta, x=x, y=y)
        time.sleep(0.3)

    def chiudi_sessione(self) -> None:
        """Chiude la connessione RDP terminando il processo mstsc."""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
                logger.info("Sessione RDP chiusa")
            except Exception as e:
                logger.warning(f"Errore durante la chiusura RDP: {e}")
            finally:
                self._process = None
                self._window_hwnd = None

    def __enter__(self):
        self.apri_sessione()
        return self

    def __exit__(self, *args):
        self.chiudi_sessione()
