"""Static registry of Italian-market car brands and models.

Used by the relevance scorer to:
- Generate model_variants (name variations for search)
- Generate exclude_models (same-brand models to filter out off-topic results)
- Generate brand_aliases (VW -> Volkswagen, etc.)
"""

BRAND_MODELS = {
    "Volkswagen": {
        "aliases": ["VW"],
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
        "models": {
            "Panda": {"variants": ["Panda Cross", "Panda Hybrid", "Pandina"]},
            "500": {"variants": ["500e", "Cinquecento"]},
            "500X": {"variants": []},
            "Tipo": {"variants": ["Tipo Cross", "Tipo Station Wagon"]},
            "600": {"variants": ["600e"]},
            "Doblò": {"variants": ["Doblo"]},
        },
    },
    "Alfa Romeo": {
        "aliases": ["Alfa"],
        "models": {
            "Giulia": {"variants": ["Giulia Quadrifoglio"]},
            "Stelvio": {"variants": ["Stelvio Quadrifoglio"]},
            "Tonale": {"variants": []},
            "Junior": {"variants": []},
        },
    },
    "Jeep": {
        "aliases": [],
        "models": {
            "Renegade": {"variants": ["Renegade 4xe"]},
            "Compass": {"variants": ["Compass 4xe"]},
            "Avenger": {"variants": ["Avenger e-Hybrid"]},
            "Wrangler": {"variants": []},
        },
    },
    "Toyota": {
        "aliases": [],
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
        "models": {
            "C3": {"variants": ["C3 Aircross", "e-C3"]},
            "C4": {"variants": ["C4 X", "e-C4"]},
            "C5 Aircross": {"variants": ["C5Aircross"]},
            "Berlingo": {"variants": []},
        },
    },
    "BMW": {
        "aliases": [],
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
        "models": {
            "Sandero": {"variants": ["Sandero Stepway"]},
            "Duster": {"variants": []},
            "Jogger": {"variants": ["Jogger Hybrid"]},
            "Spring": {"variants": []},
        },
    },
    "Opel": {
        "aliases": [],
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
        "models": {
            "Ypsilon": {"variants": ["Nuova Ypsilon"]},
        },
    },
    "Abarth": {
        "aliases": [],
        "models": {
            "500": {"variants": ["500e", "595", "695"]},
        },
    },
    "DS": {
        "aliases": ["DS Automobiles"],
        "models": {
            "DS 3": {"variants": ["DS3 Crossback"]},
            "DS 4": {"variants": ["DS4"]},
            "DS 7": {"variants": ["DS7 Crossback", "DS7"]},
        },
    },
    "Tesla": {
        "aliases": [],
        "models": {
            "Model 3": {"variants": ["Model3"]},
            "Model Y": {"variants": ["ModelY"]},
            "Model S": {"variants": ["ModelS"]},
            "Model X": {"variants": ["ModelX"]},
        },
    },
    "Nissan": {
        "aliases": [],
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
        "models": {
            "Ibiza": {"variants": []},
            "Arona": {"variants": []},
            "Leon": {"variants": ["León"]},
            "Ateca": {"variants": []},
        },
    },
    "Cupra": {
        "aliases": [],
        "models": {
            "Formentor": {"variants": []},
            "Born": {"variants": []},
            "Leon": {"variants": ["León"]},
            "Tavascan": {"variants": []},
        },
    },
    "MG": {
        "aliases": [],
        "models": {
            "ZS": {"variants": ["ZS EV"]},
            "MG4": {"variants": ["MG 4"]},
            "HS": {"variants": []},
            "Marvel R": {"variants": []},
        },
    },
    "Volvo": {
        "aliases": [],
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
    brand_lower = brand.lower()
    brand_entry = None
    brand_key = None

    for key, data in BRAND_MODELS.items():
        if key.lower() == brand_lower:
            brand_entry = data
            brand_key = key
            break
        if any(a.lower() == brand_lower for a in data["aliases"]):
            brand_entry = data
            brand_key = key
            break

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
