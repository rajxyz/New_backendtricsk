import json
from pathlib import Path

CACHE_PATH = Path("data/abbreviations.json")

def load_cache():
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_to_cache(new_entry):
    cache = load_cache()
    if any(e['abbr'].lower() == new_entry['abbr'].lower() for e in cache):
        return  # Skip if duplicate
    cache.append(new_entry)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
