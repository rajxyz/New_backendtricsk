import json
import random
import logging
import re
from fastapi import APIRouter, Query
from pathlib import Path
from enum import Enum

from .generate_template_sentence import generate_template_sentence, load_templates

# Setup
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
    generate_sentence = "generate_sentence"

DATA_FILE_MAP = {
    "abbreviations": "data.json",
    "generate_sentence": "wordbank.json"
}

TEMPLATE_FILE_MAP = {
    "generate_sentence": "English_templates.json"
}

wordbank_cache = None

def load_json(file_key):
    file_path = BASE_DIR / DATA_FILE_MAP[file_key]
    if not file_path.exists():
        logger.warning(f"[{file_key.upper()}] File not found: {file_path}")
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

    # --- ABBREVIATIONS ---
    if type == TrickType.abbreviations:
        data = load_json("abbreviations")
        nouns = data.get("nouns", {})
        preps = data.get("prepositions", {})
        trick_words = []

        for i, letter in enumerate(input_parts):
            if i % 2 == 1:  # Preposition
                word_list = preps.get(letter, []) or preps.get("_default", [])
            else:  # Noun
                word_list = nouns.get(letter, [])

            if word_list:
                trick_words.append(random.choice(word_list))
            else:
                trick_words.append("???")

        trick = " ".join(trick_words)

        if "???" in trick:
            return {"trick": random.choice(default_lines)}
        return {"trick": trick}

    # --- GENERATE SENTENCE ---
    elif type == TrickType.generate_sentence:
        if wordbank_cache is None:
            wordbank_cache = load_json("generate_sentence")

        templates = load_templates(TEMPLATE_FILE_MAP["generate_sentence"])
        if not templates:
            return {"trick": "No templates found."}

        template = random.choice(templates)
        sentence = generate_template_sentence(
            template,
            wordbank_cache,
            input_parts
        )
        return {"trick": sentence}

    return {"trick": "Invalid trick type selected."}
