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
    nickname = "nickname"

DATA_FILE_MAP = {
    "abbreviations": "data.json",
    "generate_sentence": "wordbank.json",
    "nickname": "nickname_data.json"
}

TEMPLATE_FILE_MAP = {
    "generate_sentence": "routes/English_templates.json",
    "nickname": "routes/nickname_templates.json"
}

wordbank_cache = None
nickname_cache = None

def load_json(file_key):
    file_path = BASE_DIR / DATA_FILE_MAP[file_key]
    if not file_path.exists():
        logger.warning(f"[{file_key.upper()}] File not found: {file_path}")
        return {}
    with file_path.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

        normalized_data = {}
        for key, value in raw_data.items():
            if isinstance(value, dict):
                normalized_data[key.lower()] = {k.upper(): v for k, v in value.items()}
            else:
                normalized_data[key.lower()] = value
        return normalized_data

def load_template_json(file_key):
    file_path = BASE_DIR / TEMPLATE_FILE_MAP[file_key]
    if not file_path.exists():
        logger.warning(f"[TEMPLATES-{file_key.upper()}] File not found: {file_path}")
        return {}
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f).get("TEMPLATES_BY_LENGTH", {})

def extract_letters(input_str):
    input_str = re.sub(r"[^a-zA-Z,\s]", "", input_str).strip()

    if "," in input_str:
        parts = [p.strip() for p in input_str.split(",") if p.strip()]
        if all(len(p) > 1 for p in parts):
            return [word[0].upper() for word in parts]
        return [p.upper() for p in parts]

    if re.fullmatch(r"[a-zA-Z]+", input_str):
        if len(input_str) <= 5:
            return list(input_str.upper())
        else:
            return [ch[0].upper() for ch in re.findall(r'[A-Z][a-z]*', input_str) or input_str]

    words = re.findall(r'\b\w+', input_str)
    return [w[0].upper() for w in words if w]

@router.get("/api/tricks")
def get_tricks(
    type: TrickType = Query(..., description="Type of trick"),
    letters: str = Query(..., description="Comma-separated letters or words")
):
    global wordbank_cache, nickname_cache
    logger.info(f"[API] Trick Type: {type}")
    logger.info(f"[API] Input Letters Raw: {letters}")

    input_parts = extract_letters(letters)
    logger.info(f"[DEBUG] Normalized Input Letters: {input_parts}")

    if not input_parts:
        return {"trick": "Invalid input."}

    if type == TrickType.nickname:
        if nickname_cache is None:
            nickname_cache = load_json("nickname")
            logger.debug(f"[LOADED NICKNAME DATA] Letters: {list(nickname_cache.keys())}")

        template_data = load_template_json("nickname")
        letter_count = str(len(input_parts))
        logger.info(f"[DEBUG] Nickname Template length group: {letter_count}")

        matching_templates = template_data.get(letter_count, [])

        if not matching_templates:
            logger.warning(f"[DEBUG] No nickname templates found for length: {letter_count}")
            return {"trick": random.choice(default_lines)}

        max_attempts = 10
        for attempt in range(max_attempts):
            template = random.choice(matching_templates)
            logger.info(f"[DEBUG] Attempt {attempt+1}: Trying Nickname Template: {template}")

            placeholders = re.findall(r"\{(\w+)\}", template)

            if len(placeholders) != len(input_parts):
                logger.info(f"[⚠️] Skipping nickname template due to placeholder/letter mismatch.")
                continue

            words = {}
            success = True

            for placeholder, letter in zip(placeholders, input_parts):
                word_list = nickname_cache.get(letter.upper(), []) or nickname_cache.get("_default", [])

                if not word_list:
                    success = False
                    break

                selected_word = random.choice(word_list)
                words[placeholder] = selected_word

            if success:
                final_sentence = template
                for key, val in words.items():
                    final_sentence = final_sentence.replace(f"{{{key}}}", val, 1)

                return {"trick": final_sentence}

        return {"trick": random.choice(default_lines)}

    elif type == TrickType.abbreviations:
        data = load_json("abbreviations")
        nouns = data.get("nouns", {})
        preps = data.get("prepositions", {})
        trick_words = []

        for i, letter in enumerate(input_parts):
            if i % 2 == 1:
                word_list = preps.get(letter, []) or preps.get("_default", [])
            else:
                word_list = nouns.get(letter, []) or nouns.get("_default", [])

            if word_list:
                word = random.choice(word_list)
                trick_words.append(word)
            else:
                trick_words.append("???")

        trick = " ".join(trick_words)

        if "???" in trick:
            return {"trick": random.choice(default_lines)}
        return {"trick": trick}

    elif type == TrickType.generate_sentence:
        if wordbank_cache is None:
            wordbank_cache = load_json("generate_sentence")

        template_data = load_template_json("generate_sentence")
        letter_count = str(len(input_parts))

        matching_templates = template_data.get(letter_count, [])

        if not matching_templates:
            return {"trick": "No matching templates for this input length."}

        max_attempts = 10
        for attempt in range(max_attempts):
            template = random.choice(matching_templates)
            placeholders = re.findall(r"\{(\w+)\}", template)

            if len(placeholders) != len(input_parts):
                continue

            words = {}
            success = True

            for placeholder, letter in zip(placeholders, input_parts):
                base = placeholder.rstrip("s").lower()
                category = base + "s"

                if category not in wordbank_cache:
                    success = False
                    break

                word_list = wordbank_cache[category].get(letter.upper(), []) or wordbank_cache[category].get("_default", [])

                if not word_list:
                    success = False
                    break

                selected_word = random.choice(word_list)
                words[placeholder] = selected_word

            if success:
                final_sentence = template
                for key, val in words.items():
                    final_sentence = final_sentence.replace(f"{{{key}}}", val, 1)

                return {"trick": final_sentence}

        return {"trick": "Couldn't generate a sentence using all letters."}

    return {"trick": "Invalid trick type selected."}
      
