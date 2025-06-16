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

# Setup
router = APIRouter()
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

# Default fallback messages
default_lines = [
    "Iska trick abhi update nahi hua.",
    "Agle version me iski baari aayegi.",
    "Filhal kuch khaas nahi bola ja sakta.",
    "Yeh abhi training me hai, ruk ja thoda!"
]

# Trick Type Enum
class TrickType(str, Enum):
    abbreviations = "abbreviations"
    simple_sentence = "simple_sentence"

# File mapping
DATA_FILE_MAP = {
    "abbreviations": "data.json",
    "simple_sentence": "wordbank.json"
}

TEMPLATE_FILE_MAP = {
    "simple_sentence": "English_templates.json"
}

# Cache
wordbank_cache = None

# Load abbreviation data
def load_entities_abbr():
    file_path = BASE_DIR / DATA_FILE_MAP["abbreviations"]
    logger.debug(f"[ABBR] Loading from: {file_path}")
    if not file_path.exists():
        logger.warning(f"[ABBR] File not found: {file_path}")
        return []
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)

# Load wordbank data
def load_wordbank():
    file_path = BASE_DIR / DATA_FILE_MAP["simple_sentence"]
    logger.debug(f"[WORDBANK] Loading from: {file_path}")
    if not file_path.exists():
        logger.warning(f"[WORDBANK] File not found: {file_path}")
        return {}
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)

# Normalize input like "ltm", "l,t,m", "lotus torch mango"
def extract_letters(input_str):
    if "," in input_str:
        parts = [p.strip() for p in input_str.split(",") if p.strip()]
    elif re.match(r"^[a-zA-Z]+$", input_str.strip()):
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
    logger.debug(f"[API] Normalized Input: {input_parts}")

    if not input_parts:
        logger.warning("[API] Empty input letters!")
        return {"trick": "Invalid input."}

    # ---- ABBREVIATIONS ----
    if type == TrickType.abbreviations:
        query = ''.join(input_parts).lower()
        logger.info(f"[ABBR] Searching for abbreviation: '{query}'")

        data = load_entities_abbr()
        matched = [item for item in data if item.get("abbr", "").lower() == query]

        if matched:
            item = matched[0]
            return {
                "trick": f"{item['abbr']} — {item['full_form']}: {item['description']}"
            }

        logger.info("[ABBR] No match found in local data.")
        return {"trick": random.choice(default_lines)}

    # ---- SIMPLE SENTENCE ----
    elif type == TrickType.simple_sentence:
        if wordbank_cache is None:
            wordbank_cache = load_wordbank()

        templates = load_template_sentences(TEMPLATE_FILE_MAP["simple_sentence"])
        if not templates:
            logger.warning("[SENTENCE] No templates found.")
            return {"trick": "No templates found."}

        template = random.choice(templates)
        sentence = generate_template_sentence(
            template,
            wordbank_cache,
            [l.upper() for l in input_parts]
        )
        return {"trick": sentence}

    # ---- INVALID TYPE ----
    logger.warning("[API] Invalid trick type selected.")
    return {"trick": "Invalid trick type selected."}
