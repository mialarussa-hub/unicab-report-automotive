"""Canonical vocabulary for fuel type (alimentazione) and engine displacement (cilindrata).

Used by AI prompts to tag extracted items/comments with structured motore info,
and by filter logic to match requested alimentazione/cilindrata against data.
"""

from __future__ import annotations

# Canonical alimentazione values emitted by the AI prompts and used for filtering.
# Italian labels are shown in the UI dropdown.
ALIMENTAZIONE_CANONICA = [
    "benzina",
    "diesel",
    "gpl",
    "metano",
    "elettrico",
    "ibrido_full",    # HEV — full hybrid (Toyota HSD, e-CVT style)
    "ibrido_mild",    # MHEV — mild hybrid (48V assist)
    "ibrido_plugin",  # PHEV — plug-in hybrid
]

ALIMENTAZIONE_LABEL_IT = {
    "benzina": "Benzina",
    "diesel": "Diesel",
    "gpl": "GPL",
    "metano": "Metano",
    "elettrico": "Elettrico",
    "ibrido_full": "Ibrido Full (HEV)",
    "ibrido_mild": "Ibrido Mild (MHEV)",
    "ibrido_plugin": "Ibrido Plug-in (PHEV)",
}


def prompt_enum_description() -> str:
    """Human-readable description of the enum for embedding in AI prompts."""
    return (
        "benzina | diesel | gpl | metano | elettrico | "
        "ibrido_full (full hybrid / HEV, NON plug-in) | "
        "ibrido_mild (48V mild hybrid / MHEV) | "
        "ibrido_plugin (plug-in hybrid / PHEV)"
    )


def normalize_cilindrata(value) -> float | None:
    """Normalize a displacement value to a single-decimal float in liters.

    Accepts: 1.0 | "1.0" | "1000" | "1000cc" | "999" | "0.999" → 1.0
    Returns None if not parseable or outside plausible range.
    """
    if value is None or value == "":
        return None
    try:
        if isinstance(value, str):
            s = value.strip().lower().replace(",", ".")
            # strip trailing units
            for unit in ("cc", "cm3", "cm³", "l", "liters", "liter", "litri"):
                if s.endswith(unit):
                    s = s[: -len(unit)].strip()
            num = float(s)
        else:
            num = float(value)
    except (ValueError, TypeError):
        return None

    # Heuristic: values > 50 are likely cc (999, 1600, 1998 …)
    if num > 50:
        num = num / 1000.0

    # Round to 1 decimal place ("litrage" convention: 0.9, 1.0, 1.2, 1.4 …)
    num = round(num + 1e-9, 1)

    if num < 0.5 or num > 8.5:
        return None
    return num


def normalize_alimentazione(value) -> str | None:
    """Map a free-text alimentazione to canonical enum, or None if unknown."""
    if not value:
        return None
    s = str(value).strip().lower()
    if s in ALIMENTAZIONE_CANONICA:
        return s

    # Simple fuzzy mapping for free-text inputs from AI or users
    mapping = {
        "gasoline": "benzina", "petrol": "benzina", "bz": "benzina",
        "gasolio": "diesel", "dsl": "diesel",
        "lpg": "gpl",
        "cng": "metano", "ngv": "metano",
        "ev": "elettrico", "bev": "elettrico", "electric": "elettrico",
        "hev": "ibrido_full", "full hybrid": "ibrido_full", "hybrid": "ibrido_full",
        "mhev": "ibrido_mild", "mild hybrid": "ibrido_mild", "48v": "ibrido_mild",
        "phev": "ibrido_plugin", "plug-in": "ibrido_plugin",
        "plug in": "ibrido_plugin", "plugin": "ibrido_plugin",
    }
    return mapping.get(s)


def motori_match(motore_info: dict | None, want_alim: str | None,
                 want_cil: float | None) -> bool:
    """Return True if a motore_info dict matches the requested filter.

    motore_info shape (per-item): {"versioni": [{"alimentazione": str, "cilindrata": float|None}, ...]}
                  or (per-comment): {"alimentazione": str, "cilindrata": float|None}
    A None/empty motore_info never matches a positive filter.
    """
    if not want_alim and not want_cil:
        return True  # no filter → trivially matches

    if not motore_info:
        return False

    # Flatten: item-level may have list under "versioni"; comment-level is flat.
    candidates = []
    if isinstance(motore_info, dict):
        versioni = motore_info.get("versioni")
        if isinstance(versioni, list) and versioni:
            candidates = versioni
        else:
            candidates = [motore_info]

    for m in candidates:
        if not isinstance(m, dict):
            continue
        m_alim = normalize_alimentazione(m.get("alimentazione"))
        m_cil = normalize_cilindrata(m.get("cilindrata"))
        if want_alim and m_alim != want_alim:
            continue
        if want_cil and m_cil != want_cil:
            continue
        return True
    return False
