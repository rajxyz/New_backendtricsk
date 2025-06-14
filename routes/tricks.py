import json
import random
import logging
import re
from fastapi import APIRouter, Query
from pathlib import Path
from enum import Enum

from .generate_template_sentence import (
    generate_template_sentence,
    load_templates as load_template_sentences
)

# Wikipedia + other fetch tools
from wiki_utils import fetch_abbreviation_details
from cache import save_to_cache

router = APIRouter()
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

default_lines = [
    "Iska trick abhi update nahi hua.",
    "Agle version me iski baari aayegi.",
    "Filhal kuch khaas nahi bola ja sakta.",
    "Yeh abhi training me hai, ruk ja thoda!"
]

class TrickType(str, Enum):
    abbreviations = "abbreviations"
    simple_sentence = "simple_sentence"

DATA_FILE_MAP = {
    "abbreviations": "data.json",
    "simple_sentence": "wordbank.json"
}

TEMPLATE_FILE_MAP = {
    "simple_sentence": "English_templates.json"
}

wordbank_cache = None

def load_entities_abbr():
    file_path = BASE_DIR / DATA_FILE_MAP["abbreviations"]
    logger.debug(f"[ABBR] Loading from: {file_path}")
    if not file_path.exists():
        logger.warning(f"[ABBR] File not found: {file_path}")
        return []
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        logger.debug(f"[ABBR] Loaded {len(data)} records")
        return data

def load_wordbank():
    file_path = BASE_DIR / DATA_FILE_MAP["simple_sentence"]
    logger.debug(f"[WORDBANK] Loading from: {file_path}")
    if not file_path.exists():
        logger.warning(f"[WORDBANK] File not found: {file_path}")
        return {}
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        logger.debug(f"[WORDBANK] Loaded categories: {list(data.keys())}")
        return data

# 🆕 NEW: Normalize input to handle l,t,m or ltm or lotus,torch,mango etc
def extract_letters(input_str):
    if "," in input_str:
        parts = [p.strip() for p in input_str.split(",") if p.strip()]
    else:
        # Single word or continuous letters
        if re.match(r"^[a-zA-Z]+$", input_str.strip()):
            parts = list(input_str.strip())
        else:
            parts = [w.strip() for w in re.findall(r'\b\w+\b', input_str)]
    return parts

@router.get("/api/tricks")
def get_tricks(
    type: TrickType = Query(..., description="Type of trick"),
    letters: str = Query(..., description="Comma-separated letters or words")
):
    global wordbank_cache
    logger.info(f"[API] Trick Type: {type}")
    logger.info(f"[API] Input Letters Raw: {letters}")

    input_parts = extract_letters(letters)
    logger.debug(f"[API] Normalized Input Letters/Words: {input_parts}")

    if not input_parts:
        logger.warning("[API] Empty input letters!")
        return {"trick": "Invalid input."}

    # ---- ABBREVIATIONS TRICK ----
    if type == TrickType.abbreviations:
        query = ''.join(input_parts).lower()
        logger.info(f"[ABBR] Searching for abbreviation: '{query}'")
        data = load_entities_abbr()
        matched = [item for item in data if item.get("abbr", "").lower() == query]
        logger.debug(f"[ABBR] Matches found: {len(matched)}")

        if matched:
            item = matched[0]
            return {
                "trick": f"{item['abbr']} — {item['full_form']}: {item['description']}"
            }

        logger.info(f"[WIKI] No match found in local data, trying Wikipedia for '{query.upper()}'")
        wiki_data = fetch_abbreviation_details(query)
        logger.debug(f"[WIKI] Wikipedia fetch result: {wiki_data}")

        # Load wordbank if not already cached
        if wordbank_cache is None:
            wordbank_cache = load_wordbank()

        # Try building abbreviation from letters using wordbank
        built_words = []
        for i, letter in enumerate(input_parts):
            letter = letter.upper()
            possible_words = []

            for category in ['nouns', 'adjectives']:
                if letter in wordbank_cache.get(category, {}):
                    possible_words += wordbank_cache[category][letter]

            built_word = random.choice(possible_words).capitalize() if possible_words else letter
            built_words.append(built_word)

        built_full_form = " ".join(built_words)

        trick_output = f"{query.upper()} — {built_full_form}"
        if wiki_data["full_form"] != "Not found":
            trick_output += f": {wiki_data['description']}"
        else:
            trick_output += ": Description not available."

        save_to_cache({
            "abbr": query.upper(),
            "full_form": built_full_form,
            "description": wiki_data.get("description", "No description.")
        })

        return {"trick": trick_output}

    # ---- SIMPLE SENTENCE TRICK ----
    elif type == TrickType.simple_sentence:
        logger.info("[SENTENCE] Generating simple sentence trick")

        if wordbank_cache is None:
            logger.debug("[SENTENCE] Loading wordbank into cache")
            wordbank_cache = load_wordbank()

        templates = load_template_sentences(TEMPLATE_FILE_MAP["simple_sentence"])
        logger.debug(f"[SENTENCE] Loaded {len(templates)} templates")

        if not templates:
            logger.warning("[SENTENCE] No templates found.")
            return {"trick": "No templates found."}

        template = random.choice(templates)
        logger.debug(f"[SENTENCE] Selected template: {template}")

        sentence = generate_template_sentence(
            template,
            wordbank_cache,
            [l.upper() for l in input_parts]
        )

        logger.info(f"[SENTENCE] Final sentence: {sentence}")
        return {"trick": sentence}

    # ---- INVALID TYPE ----
    logger.warning("[API] Invalid trick type selected.")
    return {"trick": "Invalid trick type selected."}
