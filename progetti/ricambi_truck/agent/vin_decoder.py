# vin_decoder.py
# Identifica il marchio del veicolo a partire dal prefisso WMI del numero di telaio (VIN)

from typing import Optional

# Mappa WMI → marchio (World Manufacturer Identifier, primi 3 caratteri del VIN)
# Fonte: standard ISO 3779 + registri ufficiali costruttori truck europei
WMI_MAP: dict[str, str] = {
    # IVECO
    "ZFA": "IVECO",
    "ZCF": "IVECO",
    "ZFF": "IVECO",  # anche FIAT veicoli commerciali
    "ZGU": "IVECO",
    "ZGB": "IVECO",
    "ZGT": "IVECO",
    "ZGH": "IVECO",
    "ZGK": "IVECO",
    "ZLA": "IVECO",  # IVECO Bus / Irisbus

    # SCANIA
    "YS2": "SCANIA",
    "YS3": "SCANIA",

    # MAN
    "WMA": "MAN",
    "WMN": "MAN",
    "WMW": "MAN",  # anche MINI ma non rilevante
    "WMK": "MAN",

    # DAF
    "XLR": "DAF",
    "XLD": "DAF",
    "XLB": "DAF",
    "XLF": "DAF",

    # VOLVO
    "YV2": "VOLVO",
    "YV1": "VOLVO",
    "YV3": "VOLVO",

    # RENAULT TRUCKS
    "VF6": "RENAULT",
    "VF3": "RENAULT",
    "VF1": "RENAULT",

    # MERCEDES-BENZ Trucks
    "WDB": "MERCEDES",
    "WDC": "MERCEDES",
    "WDD": "MERCEDES",
    "WEB": "MERCEDES",

    # FORD TRUCKS (meno comune ma presente)
    "WF0": "FORD",

    # DENNIS / DENNIS EAGLE (UK, meno comune)
    "SAF": "DENNIS",
}

# Mappa alternativa per corrispondenza parziale su prefisso di 2 caratteri
# usata come fallback se i 3 caratteri non matchano
WMI_PREFIX_2: dict[str, str] = {
    "ZF": "IVECO",
    "ZC": "IVECO",
    "ZL": "IVECO",
    "YS": "SCANIA",
    "YV": "VOLVO",
    "XL": "DAF",
    "WM": "MAN",
    "WD": "MERCEDES",
    "WE": "MERCEDES",
    "VF": "RENAULT",
}


def decode_vin(telaio: str) -> Optional[str]:
    """
    Restituisce il nome del marchio del veicolo dato il telaio (VIN).
    Prova prima con i primi 3 caratteri (WMI), poi con i primi 2 come fallback.
    Ritorna None se il marchio non è riconosciuto.
    """
    telaio = telaio.strip().upper().replace(" ", "").replace("-", "")

    if len(telaio) < 3:
        return None

    wmi3 = telaio[:3]
    if wmi3 in WMI_MAP:
        return WMI_MAP[wmi3]

    # Fallback a 2 caratteri
    wmi2 = telaio[:2]
    if wmi2 in WMI_PREFIX_2:
        return WMI_PREFIX_2[wmi2]

    return None


def get_marchi_supportati() -> list[str]:
    """Restituisce la lista dei marchi supportati dal sistema."""
    return sorted(set(WMI_MAP.values()))


# Test rapido se eseguito direttamente
if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    test_telai = [
        ("ZFA6H0000S1234567", "IVECO"),
        ("YS2R4X20004123456", "SCANIA"),
        ("WMA06XZZ8KP123456", "MAN"),
        ("XLR0197007A123456", "DAF"),
        ("YV2A4C1A8JB123456", "VOLVO"),
        ("VF626GGB0DM123456", "RENAULT"),
        ("WDB9634031L123456", "MERCEDES"),
        ("ZLA456789012345678", "IVECO"),
        ("ABC123", None),
    ]
    print("Test VIN Decoder:")
    for telaio, atteso in test_telai:
        risultato = decode_vin(telaio)
        stato = "✅" if risultato == atteso else "❌"
        print(f"  {stato} {telaio[:10]}... → {risultato} (atteso: {atteso})")
