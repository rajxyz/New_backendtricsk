import json
import os
from pathlib import Path

CACHE_PATH = Path("data/abbreviations.json")

def load_cache():
    print(f"[DEBUG] Current working directory: {os.getcwd()}")
    print(f"[DEBUG] Absolute path to cache file: {CACHE_PATH.resolve()}")
    print(f"[DEBUG] Loading cache from: {CACHE_PATH}")

    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                print(f"[DEBUG] Loaded {len(data)} entries from cache.")
                return data
            except json.JSONDecodeError:
                print("[ERROR] JSON decode error — file is empty or malformed. Returning empty dict.")
                return {}
    print("[DEBUG] Cache file not found. Returning empty dict.")
    return {}

def save_to_cache(new_entry):
    print(f"[DEBUG] Trying to save: {new_entry}")
    cache = load_cache()
    key = new_entry['abbr'].lower()

    if key in cache:
        print(f"[DEBUG] Entry '{new_entry['abbr']}' already exists in cache. Skipping save.")
        return

    cache[key] = new_entry
    
    # Ensure parent directory exists
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
        print(f"[DEBUG] Saved new entry for '{new_entry['abbr']}' to cache.")
        print(f"[DEBUG] Written to: {CACHE_PATH.resolve()}")
