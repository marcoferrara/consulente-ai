# image_annotator.py
# Annota gli screenshot con un cerchio rosso attorno al particolare trovato

import os
import tempfile
import logging
from typing import Optional, Tuple
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

# Colore e spessore del cerchio di evidenziazione
COLORE_CERCHIO = (220, 38, 38)   # Rosso (#DC2626)
SPESSORE_CERCHIO = 4
RAGGIO_DEFAULT = 40              # Raggio del cerchio se non specificato


def evidenzia_coordinate(
    img: Image.Image,
    x: int,
    y: int,
    raggio: int = RAGGIO_DEFAULT,
) -> Image.Image:
    """
    Disegna un cerchio rosso centrato su (x, y) sullo screenshot.
    Restituisce una nuova immagine annotata (non modifica l'originale).
    """
    img_annotata = img.copy().convert("RGB")
    draw = ImageDraw.Draw(img_annotata)

    # Rettangolo di bounding box per l'ellisse
    bbox = [
        x - raggio,
        y - raggio,
        x + raggio,
        y + raggio,
    ]

    # Cerchio pieno semi-trasparente come sfondo
    overlay = Image.new("RGBA", img_annotata.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    draw_overlay.ellipse(bbox, fill=(*COLORE_CERCHIO, 50))  # 50/255 opacità
    img_rgba = img_annotata.convert("RGBA")
    img_rgba = Image.alpha_composite(img_rgba, overlay)
    img_annotata = img_rgba.convert("RGB")

    # Cerchio bordo spesso
    draw2 = ImageDraw.Draw(img_annotata)
    for i in range(SPESSORE_CERCHIO):
        bbox_spessore = [
            x - raggio - i,
            y - raggio - i,
            x + raggio + i,
            y + raggio + i,
        ]
        draw2.ellipse(bbox_spessore, outline=COLORE_CERCHIO)

    return img_annotata


def salva_screenshot_annotato(
    img: Image.Image,
    x: int,
    y: int,
    nome_file: Optional[str] = None,
    raggio: int = RAGGIO_DEFAULT,
) -> str:
    """
    Evidenzia il punto (x, y) nello screenshot e salva il file PNG.
    Restituisce il percorso del file salvato.
    """
    img_annotata = evidenzia_coordinate(img, x, y, raggio)

    if nome_file:
        percorso = nome_file
    else:
        # File temporaneo nella cartella temp di sistema
        fd, percorso = tempfile.mkstemp(suffix=".png", prefix="truck_screenshot_")
        os.close(fd)

    img_annotata.save(percorso, format="PNG", optimize=True)
    logger.debug(f"Screenshot annotato salvato in: {percorso}")
    return percorso


def annotazione_multipla(
    img: Image.Image,
    punti: list[Tuple[int, int]],
    raggi: Optional[list[int]] = None,
) -> Image.Image:
    """
    Disegna più cerchi sullo stesso screenshot per annotare più elementi.
    Utile quando più codici si trovano nella stessa tavola.
    """
    img_annotata = img.copy()
    for i, (x, y) in enumerate(punti):
        raggio = raggi[i] if raggi and i < len(raggi) else RAGGIO_DEFAULT
        img_annotata = evidenzia_coordinate(img_annotata, x, y, raggio)
    return img_annotata
