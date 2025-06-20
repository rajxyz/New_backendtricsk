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
logging.basicConfig(level=logging.DEBUG)

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
    "simple_sentence": {
        "default": "English_templates.json",
        "custom_by_length": {
            5: {
                "actor": "templates_actor_5.json",
                "animal": "templates_animal_5.json",
                "cricketer": "templates_cricketer_5.json"
            },
            6: {
                "actor": "templates_actor_6.json",
                "animal": "templates_animal_6.json",
                "cricketer": "templates_cricketer_6.json"
            },
            7: {
                "actor": "templates_actor_7.json",
                "animal": "templates_animal_7.json",
                "cricketer": "templates_cricketer_7.json"
            },
            8: {
                "actor": "templates_actor_8.json",
                "animal": "templates_animal_8.json",
                "cricketer": "templates_cricketer_8.json"
            },
            9: {
                "actor": "templates_actor_9.json",
                "animal": "templates_animal_9.json",
                "cricketer": "templates_cricketer_9.json"
            },
            10: {
                "actor": "templates_actor_10.json",
                "animal": "templates_animal_10.json",
                "cricketer": "templates_cricketer_10.json"
            }
        }
    }
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
        parts = [p.strip().upper() for p in input_str.split(",") if p.strip()]
    elif re.match(r"^[a-zA-Z]+$", input_str.strip()):
        parts = list(input_str.strip().upper())
    else:
        parts = [w[0].upper() for w in re.findall(r'\b\w+', input_str)]

    return parts

@router.get("/api/tricks")
def get_tricks(
    type: TrickType = Query(..., description="Type of trick"),
    letters: str = Query(..., description="Comma-separated letters or words"),
    category: str = Query("actor", description="Choose from: actor, animal, cricketer")
):
    global wordbank_cache

    logger.info(f"[API] Trick Type: {type}")
    logger.info(f"[API] Input Letters Raw: {letters}")

    input_parts = extract_letters(letters)
    logger.debug(f"[API] Normalized Input Letters: {input_parts}")

    if not input_parts:
        logger.warning("[API] Empty input letters!")
        return {"trick": "Invalid input."}

    # ---- ABBREVIATIONS ----
    if type == TrickType.abbreviations:
        data = load_entities_abbr()
        tricks = []
        descriptions = []

        for letter in input_parts:
            match = next(
                (item for item in data if item.get("abbr", "").upper() == letter),
                None
            )

            if match:
                noun = random.choice(match["noun"])
                template = match.get("description_template", "{noun} ek interesting concept hai.")
                tricks.append(f"{letter} — {noun}")
                descriptions.append(template.format(noun=noun))
            else:
                tricks.append(f"{letter} — ???")

        if all("???" in t for t in tricks):
            return {"trick": random.choice(default_lines)}

        return {
            "trick": ", ".join(tricks),
            "description": " ".join(descriptions)
        }

    # ---- SIMPLE SENTENCE ----
    elif type == TrickType.simple_sentence:
        if wordbank_cache is None:
            wordbank_cache = load_wordbank()

        input_length = len(input_parts)
        logger.debug(f"[SENTENCE] Letter Count: {input_length}")

        custom_templates = (
            TEMPLATE_FILE_MAP["simple_sentence"]["custom_by_length"].get(input_length)
        )

        if custom_templates and category in custom_templates:
            template_file = custom_templates[category]
            logger.debug(f"[SENTENCE] Using custom template: {template_file}")
        else:
            template_file = TEMPLATE_FILE_MAP["simple_sentence"]["default"]
            logger.debug(f"[SENTENCE] No custom template found. Using default: {template_file}")

        templates = load_template_sentences(template_file)

        if not templates:
            logger.warning("[SENTENCE] No templates found.")
            return {"trick": "No templates found."}

        template = random.choice(templates)
        logger.debug(f"[SENTENCE] Selected Template: {template}")

        sentence = generate_template_sentence(
            template,
            wordbank_cache,
            [l.upper() for l in input_parts]
        )

        return {"trick": sentence}

    logger.warning("[API] Invalid trick type selected.")
    return {"trick": "Invalid trick type selected."}
