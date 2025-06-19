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

default_lines = [
    "Iska trick abhi update nahi hua.",
    "Agle version me iski baari aayegi.",
    "Filhal kuch khaas nahi bola ja sakta.",
    "Yeh abhi training me hai, ruk ja thoda!"
]

class TrickType(str, Enum):
    abbreviations = "abbreviations"
    simple_sentence = "simple_sentence"
    logical_full_form = "logical_full_form"

DATA_FILE_MAP = {
    "abbreviations": "data.json",
    "simple_sentence": "wordbank.json",
    "logical_full_form": "data.json"
}

TEMPLATE_FILE_MAP = {
    "simple_sentence": "English_templates.json"
}

wordbank_cache = None

def load_wordbank():
    file_path = BASE_DIR / DATA_FILE_MAP["logical_full_form"]
    logger.debug(f"[LOGICAL] Loading from: {file_path}")
    if not file_path.exists():
        logger.warning(f"[LOGICAL] File not found: {file_path}")
        return {}
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)

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
        return {"trick": "Invalid input."}

    # LOGICAL FULL FORM GENERATOR
    if type == TrickType.logical_full_form:
        if len(input_parts) != 3:
            return {"trick": "Please provide exactly 3 letters."}

        data = load_wordbank()
        nouns = data.get("nouns", {})
        preps = data.get("prepositions", {})
        default_preps = preps.get("_default", ["of", "in", "for"])

        letter1, letter2, letter3 = input_parts

        noun1 = random.choice(nouns.get(letter1, [f"{letter1}-Thing"]))
        prep = random.choice(preps.get(letter2, default_preps))
        noun2 = random.choice(nouns.get(letter3, [f"{letter3}-Object"]))

        logger.info(f"[LOGICAL] Selected: {noun1} {prep} {noun2}")
        return {
            "trick": f"{noun1} {prep} {noun2}"
        }

    # FALLBACK for other types (if needed)
    return {"trick": "Only logical_full_form is supported in this version."}
