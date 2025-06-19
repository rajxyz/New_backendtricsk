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
    logical_full_form = "logical_full_form"

# File mapping
DATA_FILE_MAP = {
    "abbreviations": "data.json",
    "simple_sentence": "wordbank.json",
    "logical_full_form": "wordbank.json"
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

# Normalize input
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

    # --- ABBREVIATIONS ---
    if type == TrickType.abbreviations:
        data = load_entities_abbr()
        tricks = []
        descriptions = []

        for letter in input_parts:
            match = next((item for item in data if item.get("abbr", "").upper() == letter), None)
            if match:
                adj = random.choice(match.get("adj", []))
                noun = random.choice(match.get("noun", []))
                tricks.append(f"{letter} — {adj} {noun}")

                template = match.get("description_template")
                if template:
                    try:
                        description = template.format(adj=adj, noun=noun)
                        descriptions.append(description)
                    except Exception as e:
                        logger.error(f"Error formatting description: {e}")
            else:
                tricks.append(f"{letter} — ???")

        if all("???" in t for t in tricks):
            return {"trick": random.choice(default_lines)}

        return {
            "trick": ", ".join(tricks),
            "description": " ".join(descriptions) if descriptions else None
        }

    # --- SIMPLE SENTENCE ---
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

    # --- LOGICAL FULL FORM (Noun + Preposition + Noun) ---
    elif type == TrickType.logical_full_form:
        if len(input_parts) != 3:
            return {"trick": "Please provide exactly 3 letters."}

        wordbank = load_wordbank()
        nouns = wordbank.get("nouns", {})
        preps = wordbank.get("prepositions", {})
        default_preps = preps.get("_default", ["of", "in", "for"])

        noun1 = random.choice(nouns.get(input_parts[0], ["?"]))
        prep = random.choice(preps.get(input_parts[1], default_preps))
        noun2 = random.choice(nouns.get(input_parts[2], ["?"]))

        return {
            "trick": f"{noun1} {prep} {noun2}"
        }

    # --- Invalid Type ---
    logger.warning("[API] Invalid trick type selected.")
    return {"trick": "Invalid trick type selected."}
