import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data.json"

def load_abbreviation_data():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_abbreviation_details(term: str):
    normalized = term.replace(",", "").replace(".", "").replace(" ", "").lower()
    print(f"[DEBUG] Normalized term: {normalized}")

    data = load_abbreviation_data()

    for item in data:
        abbr = item.get("abbr", "").lower()
        if abbr == normalized:
            return {
                "abbr": item.get("abbr", "").upper(),
                "full_form": item.get("full_form", ""),
                "description": item.get("description", "")
            }

    # If not found, return a fallback
    return {
        "abbr": normalized.upper(),
        "full_form": "Not found",
        "description": "No definition found in local database."
    }
