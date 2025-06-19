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
    generate_sentence = "generate_sentence"
    abbreviations = "abbreviations"

DATA_FILE_MAP = {
    "generate_sentence": "wordbank.json",
    "abbreviations": "data.json"
}

TEMPLATE_FILE_MAP = {
    "generate_sentence": "English_templates.json"
}

wordbank_cache = None

def load_wordbank():
    file_path = BASE_DIR / DATA_FILE_MAP["abbreviations"]
    logger.info(f"[LOAD] Loading wordbank from: {file_path}")
    if not file_path.exists():
        logger.warning(f"[LOAD] Wordbank file not found: {file_path}")
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

    # 🔹 TYPE 1: generate_sentence
    if type == TrickType.generate_sentence:
        if wordbank_cache is None:
            wordbank_cache = load_wordbank()

        templates = load_template_sentences(TEMPLATE_FILE_MAP["generate_sentence"])
        if not templates:
            return {"trick": "No templates found."}

        template = random.choice(templates)
        sentence = generate_template_sentence(template, wordbank_cache, input_parts)
        return {"trick": sentence}

    # 🔹 TYPE 2: abbreviations → (noun + preposition + noun)
    elif type == TrickType.abbreviations:
        if len(input_parts) != 3:
            logger.warning("[ABBR] Invalid input length, expected 3 letters.")
            return {"trick": "Please provide exactly 3 letters."}

        data = load_wordbank()
        nouns = data.get("nouns", {})
        preps = data.get("prepositions", {})
        default_preps = preps.get("_default", ["of", "in", "for"])

        letter1, letter2, letter3 = input_parts

        logger.debug(f"[ABBR] Letters: {letter1}, {letter2}, {letter3}")
        logger.debug(f"[ABBR] Checking nouns for '{letter1}' and '{letter3}', prepositions for '{letter2}'")

        noun1 = random.choice(nouns.get(letter1, [])) if letter1 in nouns else None
        prep = random.choice(preps.get(letter2, default_preps)) if letter2 in preps or "_default" in preps else None
        noun2 = random.choice(nouns.get(letter3, [])) if letter3 in nouns else None

        if not noun1:
            logger.error(f"[ABBR] No noun found for letter '{letter1}'")
            noun1 = f"{letter1}-Thing"

        if not prep:
            logger.error(f"[ABBR] No preposition found for letter '{letter2}', using fallback.")
            prep = random.choice(default_preps)

        if not noun2:
            logger.error(f"[ABBR] No noun found for letter '{letter3}'")
            noun2 = f"{letter3}-Object"

        result = f"{noun1} {prep} {noun2}"
        logger.info(f"[ABBR] Final full form: {result}")

        return {
            "trick": result
        }

    return {"trick": "Invalid trick type selected."}
