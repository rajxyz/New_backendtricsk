import json
import random
import logging
from fastapi import APIRouter, Query
from pathlib import Path
from enum import Enum

from .generate_template_sentence import (
    generate_template_sentence,
    load_templates as load_template_sentences
)

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

@router.get("/api/tricks")
def get_tricks(
    type: TrickType = Query(..., description="Type of trick"),
    letters: str = Query(..., description="Comma-separated letters or words")
):
    global wordbank_cache
    logger.info(f"[API] Trick Type: {type}")
    logger.info(f"[API] Input Letters Raw: {letters}")

    input_parts = [w.strip() for w in letters.split(",") if w.strip()]
    logger.debug(f"[API] Cleaned Letters: {input_parts}")

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

        if not matched:
            return {"trick": f"No abbreviation found for '{query.upper()}'."}

        item = matched[0]
        logger.debug(f"[ABBR] Match: {item}")
        return {
            "trick": f"{item['abbr']} — {item['full_form']}: {item['description']}"
        }

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
