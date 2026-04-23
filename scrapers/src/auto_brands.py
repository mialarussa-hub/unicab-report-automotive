"""Static registry of Italian-market car brands and models.

Used by the relevance scorer to:
- Generate model_variants (name variations for search)
- Generate exclude_models (same-brand models to filter out off-topic results)
- Generate brand_aliases (VW -> Volkswagen, etc.)

Also stores official brand channels (website, YouTube) for L1 scraping.
"""

BRAND_MODELS = {
    "Volkswagen": {
        "aliases": ["VW"],
        "official": {
            "website": "https://www.volkswagen.it",
            "youtube_channel_id": "UC09r_PBD-CZSgGlxAtFyczg",  # Volkswagen Italia
        },
        "models": {
            "Golf": {"variants": ["Golf 8", "Golf VIII", "Golf GTI", "Golf GTE", "Golf R", "Golf Variant"]},
            "Polo": {"variants": ["Polo VI"]},
            "T-Roc": {"variants": ["TRoc", "T Roc"]},
            "T-Cross": {"variants": ["TCross", "T Cross"]},
            "Tiguan": {"variants": ["Tiguan Allspace"]},
            "Passat": {"variants": ["Passat Variant"]},
            "ID.3": {"variants": ["ID3"]},
            "ID.4": {"variants": ["ID4"]},
            "ID.7": {"variants": ["ID7"]},
            "Touareg": {"variants": []},
            "Taigo": {"variants": []},
        },
    },
    "Fiat": {
        "aliases": [],
        "official": {
            "website": "https://www.fiat.it",
            "youtube_channel_id": "UCuxWJdPJSfRKkxhRmyJmcGw",  # Fiat Italia
        },
        "models": {
            "Panda": {"variants": ["Panda Cross", "Panda Hybrid", "Pandina"]},
            "Grande Panda": {"variants": ["GrandePanda"]},
            "500": {"variants": ["500e", "Cinquecento"]},
            "500X": {"variants": []},
            "Tipo": {"variants": ["Tipo Cross", "Tipo Station Wagon"]},
            "600": {"variants": ["600e"]},
            "Doblò": {"variants": ["Doblo"]},
        },
    },
    "Alfa Romeo": {
        "aliases": ["Alfa"],
        "official": {
            "website": "https://www.alfaromeo.it",
            "youtube_channel_id": "UCRpdGxOLhHdpPa9MfHABVnA",  # Alfa Romeo
        },
        "models": {
            "Giulia": {"variants": ["Giulia Quadrifoglio"]},
            "Stelvio": {"variants": ["Stelvio Quadrifoglio"]},
            "Tonale": {"variants": []},
            "Junior": {"variants": []},
        },
    },
    "Jeep": {
        "aliases": [],
        "official": {
            "website": "https://www.jeep.it",
            "youtube_channel_id": "UCDYMMHHRuxmYkCH_LHQZOHA",  # Jeep Italia
        },
        "models": {
            "Renegade": {"variants": ["Renegade 4xe"]},
            "Compass": {"variants": ["Compass 4xe"]},
            "Avenger": {"variants": ["Avenger e-Hybrid"]},
            "Wrangler": {"variants": []},
        },
    },
    "Toyota": {
        "aliases": [],
        "official": {
            "website": "https://www.toyota.it",
            "youtube_channel_id": "UC8DIFBAsj3CwGeZj6cNDiOA",  # Toyota Italia
        },
        "models": {
            "Yaris": {"variants": ["Yaris Cross", "Yaris Hybrid"]},
            "Corolla": {"variants": ["Corolla Cross", "Corolla Touring"]},
            "C-HR": {"variants": ["CHR", "C HR"]},
            "RAV4": {"variants": ["RAV 4", "RAV4 Hybrid", "RAV4 PHEV"]},
            "Aygo X": {"variants": ["Aygo", "AygoX"]},
        },
    },
    "Renault": {
        "aliases": [],
        "official": {
            "website": "https://www.renault.it",
            "youtube_channel_id": "UCyWAyJkP-1JbUEHKw9BDew",  # Renault Italia
        },
        "models": {
            "Clio": {"variants": []},
            "Captur": {"variants": []},
            "Arkana": {"variants": []},
            "Megane E-Tech": {"variants": ["Megane", "Mégane"]},
            "Austral": {"variants": []},
            "Scenic": {"variants": ["Scénic"]},
        },
    },
    "Peugeot": {
        "aliases": [],
        "official": {
            "website": "https://www.peugeot.it",
            "youtube_channel_id": "UCYGjsRPlOm9Zjv44L1CFiNg",  # Peugeot Italia
        },
        "models": {
            "208": {"variants": ["e-208"]},
            "2008": {"variants": ["e-2008"]},
            "308": {"variants": ["e-308"]},
            "3008": {"variants": ["e-3008"]},
            "408": {"variants": []},
            "5008": {"variants": ["e-5008"]},
        },
    },
    "Citroën": {
        "aliases": ["Citroen"],
        "official": {
            "website": "https://www.citroen.it",
            "youtube_channel_id": "UCPCdxRJqaS5X4VHddBG7uOw",  # Citroën Italia
        },
        "models": {
            "C3": {"variants": ["Nuova C3"]},
            "C3 Aircross": {"variants": ["C3Aircross"]},
            "C4": {"variants": ["C4 X", "e-C4"]},
            "C5 Aircross": {"variants": ["C5Aircross"]},
            "Berlingo": {"variants": []},
        },
    },
    "BMW": {
        "aliases": [],
        "official": {
            "website": "https://www.bmw.it",
            "youtube_channel_id": "UC8S4MyWxBSgZNd-Q4FPPrwg",  # BMW Italia
        },
        "models": {
            "Serie 1": {"variants": ["118", "120", "M135"]},
            "Serie 2": {"variants": ["218", "220", "M235"]},
            "Serie 3": {"variants": ["318", "320", "330", "M340"]},
            "X1": {"variants": ["iX1"]},
            "X3": {"variants": ["iX3"]},
            "iX": {"variants": []},
            "i4": {"variants": []},
        },
    },
    "Mercedes": {
        "aliases": ["Mercedes-Benz", "MB"],
        "official": {
            "website": "https://www.mercedes-benz.it",
            "youtube_channel_id": "UCKmjnLFjolK-aW7VcBwAhLQ",  # Mercedes-Benz Italia
        },
        "models": {
            "Classe A": {"variants": ["A180", "A200", "A250", "AMG A35", "AMG A45"]},
            "Classe B": {"variants": ["B180", "B200"]},
            "Classe C": {"variants": ["C180", "C200", "C220", "C300"]},
            "GLA": {"variants": ["GLA 200", "GLA 250"]},
            "GLB": {"variants": ["GLB 200", "GLB 250"]},
            "GLC": {"variants": ["GLC 200", "GLC 300"]},
            "EQA": {"variants": []},
            "EQB": {"variants": []},
        },
    },
    "Audi": {
        "aliases": [],
        "official": {
            "website": "https://www.audi.it",
            "youtube_channel_id": "UCx_rix02WIJbMdbHn4EU1ag",  # Audi Italia
        },
        "models": {
            "A1": {"variants": []},
            "A3": {"variants": ["A3 Sportback"]},
            "A4": {"variants": ["A4 Avant"]},
            "Q2": {"variants": []},
            "Q3": {"variants": ["Q3 Sportback"]},
            "Q4 e-tron": {"variants": ["Q4 etron", "Q4"]},
            "Q5": {"variants": ["Q5 Sportback"]},
        },
    },
    "Ford": {
        "aliases": [],
        "official": {
            "website": "https://www.ford.it",
            "youtube_channel_id": "UCVfLIC3uvBVNhTfHMGvzTag",  # Ford Italia
        },
        "models": {
            "Puma": {"variants": []},
            "Kuga": {"variants": ["Kuga PHEV"]},
            "Focus": {"variants": ["Focus Active"]},
            "Fiesta": {"variants": []},
            "Mustang Mach-E": {"variants": ["Mach-E", "Mustang MachE"]},
        },
    },
    "Hyundai": {
        "aliases": [],
        "official": {
            "website": "https://www.hyundai.it",
            "youtube_channel_id": "UCR9jCAml_JkZqPQ3K-bNXJQ",  # Hyundai Italia
        },
        "models": {
            "i10": {"variants": []},
            "i20": {"variants": ["i20 N"]},
            "Tucson": {"variants": ["Tucson Hybrid", "Tucson PHEV"]},
            "Kona": {"variants": ["Kona Electric", "Kona EV"]},
            "IONIQ 5": {"variants": ["Ioniq5", "IONIQ5"]},
            "IONIQ 6": {"variants": ["Ioniq6", "IONIQ6"]},
            "Bayon": {"variants": []},
        },
    },
    "Kia": {
        "aliases": [],
        "official": {
            "website": "https://www.kia.com/it",
            "youtube_channel_id": "UCpkP1Has_yPxzn0tD7Y8F4w",  # Kia Italia
        },
        "models": {
            "Picanto": {"variants": []},
            "Stonic": {"variants": []},
            "Sportage": {"variants": ["Sportage Hybrid", "Sportage PHEV"]},
            "Niro": {"variants": ["Niro EV", "Niro PHEV", "e-Niro"]},
            "EV6": {"variants": []},
            "EV9": {"variants": []},
            "Ceed": {"variants": ["XCeed", "ProCeed"]},
        },
    },
    "Dacia": {
        "aliases": [],
        "official": {
            "website": "https://www.dacia.it",
            "youtube_channel_id": "UCN3sNcME4Fzgih2KNMtmzQ",  # Dacia Italia
        },
        "models": {
            "Sandero": {"variants": ["Sandero Stepway"]},
            "Duster": {"variants": []},
            "Jogger": {"variants": ["Jogger Hybrid"]},
            "Spring": {"variants": []},
        },
    },
    "Opel": {
        "aliases": [],
        "official": {
            "website": "https://www.opel.it",
            "youtube_channel_id": "UCjGJL3OEV3BFvfp9KFXFJFQ",  # Opel Italia
        },
        "models": {
            "Corsa": {"variants": ["Corsa-e", "Corsa Electric"]},
            "Mokka": {"variants": ["Mokka-e"]},
            "Astra": {"variants": ["Astra Sports Tourer"]},
            "Crossland": {"variants": []},
            "Grandland": {"variants": []},
        },
    },
    "Skoda": {
        "aliases": ["Škoda"],
        "official": {
            "website": "https://www.skoda.it",
            "youtube_channel_id": "UC1ULZdMcTyMJMv1Fj06YDnw",  # Škoda Italia
        },
        "models": {
            "Fabia": {"variants": []},
            "Scala": {"variants": []},
            "Octavia": {"variants": ["Octavia Wagon"]},
            "Karoq": {"variants": []},
            "Kodiaq": {"variants": []},
            "Enyaq": {"variants": ["Enyaq iV", "Enyaq Coupe"]},
            "Kamiq": {"variants": []},
        },
    },
    "Lancia": {
        "aliases": [],
        "official": {
            "website": "https://www.lancia.com",
            "youtube_channel_id": "UCZA5x3RNu3b57dX8fCBtyWg",  # Lancia
        },
        "models": {
            "Ypsilon": {"variants": ["Nuova Ypsilon"]},
        },
    },
    "Honda": {
        "aliases": [],
        "official": {
            "website": "https://www.honda.it",
            "youtube_channel_id": "UCzWIrX3m7SPT2bxQtIYXpmQ",  # Honda Italia
        },
        "models": {
            "Jazz": {"variants": ["Jazz Crosstar"]},
            "Civic": {"variants": ["Civic Type R"]},
            "HR-V": {"variants": ["HRV", "HR V"]},
            "ZR-V": {"variants": ["ZRV", "ZR V"]},
            "CR-V": {"variants": ["CRV", "CR V"]},
            "e:Ny1": {"variants": ["eNy1"]},
        },
    },
    "Mazda": {
        "aliases": [],
        "official": {
            "website": "https://www.mazda.it",
            "youtube_channel_id": "UCDjFtwLbB3bB2r72JhvnB9A",  # Mazda Italia
        },
        "models": {
            "Mazda2": {"variants": ["Mazda2 Hybrid"]},
            "Mazda3": {"variants": []},
            "CX-30": {"variants": ["CX30"]},
            "CX-5": {"variants": ["CX5"]},
            "CX-60": {"variants": ["CX60"]},
            "MX-5": {"variants": ["MX5", "Miata"]},
            "MX-30": {"variants": ["MX30"]},
        },
    },
    "DR": {
        "aliases": ["DR Automobiles"],
        "official": {
            "website": "https://www.drautomobiles.com",
            "youtube_channel_id": None,  # No dedicated YouTube channel found
        },
        "models": {
            "DR 3.0": {"variants": ["dr 3.0", "DR3"]},
            "DR 4.0": {"variants": ["dr 4.0", "DR4"]},
            "DR 5.0": {"variants": ["dr 5.0", "DR5"]},
            "DR 6.0": {"variants": ["dr 6.0", "DR6"]},
        },
    },
    "EVO": {
        "aliases": ["Evo"],
        "official": {
            "website": "https://www.evo-automobile.com",
            "youtube_channel_id": None,  # No dedicated YouTube channel found
        },
        "models": {
            "Evo 4": {"variants": ["EVO4"]},
            "Evo 5": {"variants": ["EVO5"]},
            "Evo 6": {"variants": ["EVO6"]},
            "Evo Cross 4": {"variants": []},
        },
    },
    "MG": {
        "aliases": [],
        "official": {
            "website": "https://www.mgmotor.it",
            "youtube_channel_id": "UCuYw_wGxbaBtSNrjGPUjLog",  # MG Motor Italia
        },
        "models": {
            "ZS": {"variants": ["ZS EV"]},
            "MG4": {"variants": ["MG 4"]},
            "HS": {"variants": []},
            "Marvel R": {"variants": []},
        },
    },
    "Abarth": {
        "aliases": [],
        "official": {
            "website": "https://www.abarth.it",
            "youtube_channel_id": None,
        },
        "models": {
            "500": {"variants": ["500e", "595", "695"]},
        },
    },
    "DS": {
        "aliases": ["DS Automobiles"],
        "official": {
            "website": "https://www.dsautomobiles.it",
            "youtube_channel_id": None,
        },
        "models": {
            "DS 3": {"variants": ["DS3 Crossback"]},
            "DS 4": {"variants": ["DS4"]},
            "DS 7": {"variants": ["DS7 Crossback", "DS7"]},
        },
    },
    "Tesla": {
        "aliases": [],
        "official": {
            "website": "https://www.tesla.com/it_it",
            "youtube_channel_id": None,  # Tesla doesn't have regional YouTube channels
        },
        "models": {
            "Model 3": {"variants": ["Model3"]},
            "Model Y": {"variants": ["ModelY"]},
            "Model S": {"variants": ["ModelS"]},
            "Model X": {"variants": ["ModelX"]},
        },
    },
    "Nissan": {
        "aliases": [],
        "official": {
            "website": "https://www.nissan.it",
            "youtube_channel_id": "UCpPmb_TfyDrlNjxDoqTKjAw",  # Nissan Italia
        },
        "models": {
            "Qashqai": {"variants": ["Qashqai e-Power"]},
            "Juke": {"variants": ["Juke Hybrid"]},
            "Leaf": {"variants": []},
            "X-Trail": {"variants": ["XTrail", "X Trail"]},
            "Ariya": {"variants": []},
        },
    },
    "Suzuki": {
        "aliases": [],
        "official": {
            "website": "https://auto.suzuki.it",
            "youtube_channel_id": "UCiL0bkGVdYA3QNLjHJoYoHQ",  # Suzuki Italia
        },
        "models": {
            "Swift": {"variants": []},
            "Vitara": {"variants": []},
            "S-Cross": {"variants": ["SCross", "S Cross"]},
            "Ignis": {"variants": []},
            "Jimny": {"variants": []},
        },
    },
    "Seat": {
        "aliases": ["SEAT"],
        "official": {
            "website": "https://www.seat.it",
            "youtube_channel_id": None,
        },
        "models": {
            "Ibiza": {"variants": []},
            "Arona": {"variants": []},
            "Leon": {"variants": ["León"]},
            "Ateca": {"variants": []},
        },
    },
    "Cupra": {
        "aliases": [],
        "official": {
            "website": "https://www.cupraofficial.it",
            "youtube_channel_id": None,
        },
        "models": {
            "Formentor": {"variants": []},
            "Born": {"variants": []},
            "Leon": {"variants": ["León"]},
            "Tavascan": {"variants": []},
        },
    },
    "Volvo": {
        "aliases": [],
        "official": {
            "website": "https://www.volvocars.com/it",
            "youtube_channel_id": None,
        },
        "models": {
            "XC40": {"variants": ["XC40 Recharge"]},
            "XC60": {"variants": []},
            "XC90": {"variants": []},
            "EX30": {"variants": []},
            "EX40": {"variants": []},
            "EX90": {"variants": []},
        },
    },
}


def build_model_context(brand: str, model: str) -> dict:
    """Build context dict for relevance scoring.

    Returns:
        {
            "brand": "Volkswagen",
            "model": "Golf",
            "brand_aliases": ["VW"],
            "model_variants": ["Golf 8", "Golf VIII", ...],
            "exclude_models": ["Polo", "T-Roc", "Tiguan", ...],
        }
    """
    # Find brand entry (case-insensitive, check aliases too)
    brand_entry, brand_key = _find_brand(brand)

    if not brand_entry:
        # Unknown brand — return minimal context
        return {
            "brand": brand,
            "model": model,
            "brand_aliases": [],
            "model_variants": [],
            "exclude_models": [],
        }

    # Find model entry
    model_lower = model.lower()
    model_variants = []
    exclude_models = []

    for m_name, m_data in brand_entry["models"].items():
        if m_name.lower() == model_lower:
            model_variants = list(m_data["variants"])
        else:
            exclude_models.append(m_name)

    return {
        "brand": brand_key or brand,
        "model": model,
        "brand_aliases": list(brand_entry["aliases"]),
        "model_variants": model_variants,
        "exclude_models": exclude_models,
    }


def get_official_urls(brand: str) -> dict | None:
    """Get official website and YouTube channel for a brand.

    Returns:
        {"website": "https://www.fiat.it", "youtube_channel_id": "UCxxxxx"} or None
    """
    brand_entry, _ = _find_brand(brand)
    if not brand_entry:
        return None
    return brand_entry.get("official")


def _find_brand(brand: str) -> tuple[dict | None, str | None]:
    """Find brand entry by name or alias (case-insensitive).

    Returns (brand_data, brand_key) or (None, None).
    """
    brand_lower = brand.lower()

    for key, data in BRAND_MODELS.items():
        if key.lower() == brand_lower:
            return data, key
        if any(a.lower() == brand_lower for a in data.get("aliases", [])):
            return data, key

    return None, None


def get_official_domains(brand: str) -> list[str]:
    """Registry of domains considered 'brand-owned' for L1 filtering.

    Derived from the official website host of the brand + any explicit overrides
    declared in BRAND_MODELS[brand]["official_domains"]. Used to filter out dealer
    chains, multi-brand portals, trade magazines from L1 Perplexity citations —
    Paolo's Phase A perimeter is strictly brand-owned channels.
    """
    from urllib.parse import urlparse

    entry, _ = _find_brand(brand)
    if not entry:
        return []

    domains: list[str] = []
    for d in (entry.get("official_domains") or []):
        if d:
            domains.append(d.strip().lower())

    website = (entry.get("official") or {}).get("website") or ""
    if website:
        try:
            host = urlparse(website).netloc.lower()
            if host.startswith("www."):
                host = host[4:]
            if host:
                domains.append(host)
        except Exception:
            pass

    seen: set[str] = set()
    out: list[str] = []
    for d in domains:
        if d and d not in seen:
            seen.add(d)
            out.append(d)
    return out


def is_official_domain(url: str, brand: str) -> bool:
    """True if url's host matches one of the brand's official domains (or subdomain)."""
    from urllib.parse import urlparse

    if not url:
        return False
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    if host.startswith("www."):
        host = host[4:]
    if not host:
        return False

    for d in get_official_domains(brand):
        if host == d or host.endswith("." + d):
            return True
    return False
