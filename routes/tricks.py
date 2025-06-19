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

def load_entities_abbr():
    file_path = BASE_DIR / DATA_FILE_MAP["abbreviations"]
    logger.debug(f"[ABBR] Loading from: {file_path}")
    if not file_path.exists():
        logger.warning(f"[ABBR] File not found: {file_path}")
        return []

    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, dict):  # new format: keyed by letter
            return [{"abbr": k, **v} for k, v in data.items() if isinstance(v, dict)]
        elif isinstance(data, list):
            return data
        else:
            logger.error("[ABBR] Unexpected data format in data.json")
            return []

def load_wordbank():
    file_path = BASE_DIR / DATA_FILE_MAP["logical_full_form"]
    logger.debug(f"[WORDBANK] Loading from: {file_path}")
    if not file_path.exists():
        logger.warning(f"[WORDBANK] File not found: {file_path}")
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

    if type == TrickType.abbreviations:
        data = load_entities_abbr()

        tricks = []
        descriptions = []

        for letter in input_parts:
            match = next(
                (item for item in data if isinstance(item, dict) and item.get("abbr", "").upper() == letter),
                None
            )
            if match:
                adj = random.choice(match.get("adj", [])) if match.get("adj") else ""
                noun = random.choice(match.get("noun", [])) if match.get("noun") else "???"
                tricks.append(f"{letter} — {adj} {noun}".strip())

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

    elif type == TrickType.simple_sentence:
        if wordbank_cache is None:
            wordbank_cache = load_wordbank()

        templates = load_template_sentences(TEMPLATE_FILE_MAP["simple_sentence"])
        if not templates:
            return {"trick": "No templates found."}

        template = random.choice(templates)
        sentence = generate_template_sentence(template, wordbank_cache, input_parts)
        return {"trick": sentence}

    elif type == TrickType.logical_full_form:
        if len(input_parts) != 3:
            return {"trick": "Please provide exactly 3 letters."}

        data = load_wordbank()
        nouns = data.get("nouns", {})
        preps = data.get("prepositions", {})
        default_preps = preps.get("_default", ["of", "in", "for"])

        noun1 = random.choice(nouns.get(input_parts[0], [f"{input_parts[0]}-Object"]))
        prep = random.choice(preps.get(input_parts[1], default_preps))
        noun2 = random.choice(nouns.get(input_parts[2], [f"{input_parts[2]}-Concept"]))

        return {
            "trick": f"{noun1} {prep} {noun2}"
        }

    return {"trick": "Invalid trick type selected."}
    
