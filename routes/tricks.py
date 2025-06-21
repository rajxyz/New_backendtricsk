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

router = APIRouter()
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

# Fallback messages
default_lines = [
    "Iska trick abhi update nahi hua.",
    "Agle version me iski baari aayegi.",
    "Filhal kuch khaas nahi bola ja sakta.",
    "Yeh abhi training me hai, ruk ja thoda!"
]

# Enum for trick types
class TrickType(str, Enum):
    abbreviations = "abbreviations"
    generate_sentence = "generate_sentence"

# File mappings
DATA_FILE_MAP = {
    "abbreviations": "data.json",
    "generate_sentence": "wordbank.json"
}
TEMPLATE_FILE_MAP = {
    "generate_sentence": "English_templates.json"
}

# Cache
wordbank_cache = None


# === Load abbreviation data ===
def load_entities_abbr():
    file_path = BASE_DIR / "data" / DATA_FILE_MAP["abbreviations"]
    logger.debug(f"[ABBR] Loading from: {file_path}")
    if not file_path.exists():
        logger.warning(f"[ABBR] File not found: {file_path}")
        return []
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)

# === Load wordbank data ===
def load_wordbank():
    file_path = BASE_DIR / "data" / DATA_FILE_MAP["generate_sentence"]
    logger.debug(f"[WORDBANK] Loading from: {file_path}")
    if not file_path.exists():
        logger.warning(f"[WORDBANK] File not found: {file_path}")
        return {}
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)

# === Normalize input like "ltm", "l,t,m", or "lotus torch mango" ===
def extract_letters(input_str):
    if "," in input_str:
        parts = [p.strip().upper() for p in input_str.split(",") if p.strip()]
    elif re.match(r"^[a-zA-Z]+$", input_str.strip()):
        parts = list(input_str.strip().upper())
    else:
        parts = [w[0].upper() for w in re.findall(r'\b\w+', input_str)]
    return parts


# === Main API endpoint ===
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

    # --- ABBREVIATIONS ---
    if type == TrickType.abbreviations:
        data = load_entities_abbr()
        tricks = []

        for letter in input_parts:
            match = next(
                (item for item in data if item.get("abbr", "").upper().startswith(letter)),
                None
            )
            if match:
                tricks.append(f"{letter} — {match.get('expansion', '???')}")
            else:
                tricks.append(f"{letter} — ???")

        if all("???" in t for t in tricks):
            return {"trick": random.choice(default_lines)}

        descriptions = [
            item.get("description", "")
            for item in data
            if item.get("abbr", "").upper().startswith(tuple(input_parts))
        ]

        return {
            "trick": ", ".join(tricks),
            "description": " ".join(descriptions) if descriptions else None
        }

    # --- GENERATE SENTENCE ---
    elif type == TrickType.generate_sentence:
        if wordbank_cache is None:
            wordbank_cache = load_wordbank()

        templates = load_template_sentences(TEMPLATE_FILE_MAP["generate_sentence"])
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

    # --- INVALID TYPE ---
    logger.warning("[API] Invalid trick type selected.")
    return {"trick": "Invalid trick type selected."}
