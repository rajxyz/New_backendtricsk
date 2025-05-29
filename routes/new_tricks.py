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
    "simple_sentence": "English-templates.json"
}

wordbank_cache = None

def load_entities_abbr():
    file_path = BASE_DIR / DATA_FILE_MAP["abbreviations"]
    if not file_path.exists():
        logger.warning(f"Entity data file not found: {file_path}")
        return []
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def load_wordbank():
    file_path = BASE_DIR / DATA_FILE_MAP["simple_sentence"]
    if not file_path.exists():
        logger.warning(f"Wordbank file not found: {file_path}")
        return {}
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)

@router.get("/api/tricks")
def get_tricks(
    type: TrickType = Query(..., description="Type of trick"),
    letters: str = Query(..., description="Comma-separated letters or words")
):
    global wordbank_cache
    input_parts = [w.strip() for w in letters.split(",") if w.strip()]
    if not input_parts:
        return {"trick": "Invalid input."}

    if type == TrickType.abbreviations:
        query = ''.join(input_parts).lower()
        data = load_entities_abbr()
        matched = [item for item in data if item.get("abbr", "").lower() == query]
        if not matched:
            return {"trick": f"No abbreviation found for '{query.upper()}'."}
        item = matched[0]
        return {
            "trick": f"{item['abbr']} — {item['full_form']}: {item['description']}"
        }

    elif type == TrickType.simple_sentence:
        if wordbank_cache is None:
            wordbank_cache = load_wordbank()
        templates = load_template_sentences(TEMPLATE_FILE_MAP["simple_sentence"])
        if not templates:
            return {"trick": "No templates found."}
        template = random.choice(templates)
        sentence = generate_template_sentence(
            template,
            wordbank_cache,
            [l.upper() for l in input_parts]
        )
        return {"trick": sentence}

    return {"trick": "Invalid trick type selected."}
