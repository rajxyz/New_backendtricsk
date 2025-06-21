import json
import random
import logging
import re
from fastapi import APIRouter, Query
from pathlib import Path
from enum import Enum

from .generate_template_sentence import (
    generate_template_sentence,
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
    generate_sentence = "generate_sentence"

# File mapping
DATA_FILE_MAP = {
    "abbreviations": "data.json",
    "generate_sentence": "data.json"
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
        return json.load(f).get("nouns", {})

# Load wordbank data (noun/prep/noun)
def load_wordbank():
    file_path = BASE_DIR / DATA_FILE_MAP["generate_sentence"]
    logger.debug(f"[WORDBANK] Loading from: {file_path}")
    if not file_path.exists():
        logger.warning(f"[WORDBANK] File not found: {file_path}")
        return {}
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)

# Normalize input like "ltm", "l,t,m", "lotus torch mango"
def extract_letters(input_str):
    if "," in input_str:
        parts = [p.strip().upper() for p in input_str.split(",") if p.strip()]
    elif re.match(r"^[a-zA-Z]+$", input_str.strip()):
        parts = list(input_str.strip().upper())
    else:
        parts = [w[0].upper() for w in re.findall(r'\b\w+', input_str)]
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
        data = load_entities_abbr()
        tricks = []

        for letter in input_parts:
            match = next((item for item in data.get(letter, [])), None)
            if match:
                tricks.append(f"{letter} — {match}")
            else:
                tricks.append(f"{letter} — ???")

        if all("???" in t for t in tricks):
            return {"trick": random.choice(default_lines)}

        return {
            "trick": ", ".join(tricks),
        }

    # ---- GENERATE SENTENCE ----
    elif type == TrickType.generate_sentence:
        if wordbank_cache is None:
            wordbank_cache = load_wordbank()

        if len(input_parts) != 3:
            return {"trick": "3 letters required: noun + preposition + noun"}

        noun1_letter, prep_letter, noun2_letter = input_parts

        noun1_options = wordbank_cache.get("nouns", {}).get(noun1_letter, [])
        preposition_options = wordbank_cache.get("prepositions", {}).get(prep_letter, []) or wordbank_cache.get("prepositions", {}).get("_default", [])
        noun2_options = wordbank_cache.get("nouns", {}).get(noun2_letter, [])

        if not noun1_options or not preposition_options or not noun2_options:
            return {"trick": random.choice(default_lines)}

        noun1 = random.choice(noun1_options)
        prep = random.choice(preposition_options)
        noun2 = random.choice(noun2_options)

        sentence = f"{noun1} {prep} {noun2}"
        return {"trick": sentence}

    # ---- INVALID TYPE ----
    logger.warning("[API] Invalid trick type selected.")
    return {"trick": "Invalid trick type selected."}
