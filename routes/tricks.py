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
  
# Updated path to include the 'routes' folder  
TEMPLATE_FILE_MAP = {  
    "generate_sentence": "routes/English_templates.json"  
}  
  
wordbank_cache = None  
  
def load_json(file_key):  
    file_path = BASE_DIR / DATA_FILE_MAP[file_key]  
    if not file_path.exists():  
        logger.warning(f"[{file_key.upper()}] File not found: {file_path}")  
        return {}  
    with file_path.open("r", encoding="utf-8") as f:  
        return json.load(f)  
  
def load_template_json():  
    file_path = BASE_DIR / TEMPLATE_FILE_MAP["generate_sentence"]  
    if not file_path.exists():  
        logger.warning(f"[TEMPLATES] File not found: {file_path}")  
        return {}  
    with file_path.open("r", encoding="utf-8") as f:  
        return json.load(f).get("TEMPLATES_BY_LENGTH", {})  
  
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
    logger.info(f"[DEBUG] Normalized Input: {input_parts}")  
  
    if not input_parts:  
        return {"trick": "Invalid input."}  
  
    # --- ABBREVIATIONS ---  
    if type == TrickType.abbreviations:  
        data = load_json("abbreviations")  
        nouns = data.get("nouns", {})  
        preps = data.get("prepositions", {})  
        trick_words = []  
  
        for i, letter in enumerate(input_parts):  
            if i % 2 == 1:  
                word_list = preps.get(letter, []) or preps.get("_default", [])  
            else:  
                word_list = nouns.get(letter, [])  
  
            if word_list:  
                word = random.choice(word_list)  
                trick_words.append(word)  
                logger.info(f"[DEBUG] Selected '{word}' for letter '{letter}'")  
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
  
        template_data = load_template_json()  
        letter_count = str(len(input_parts))  
        logger.info(f"[DEBUG] Template length group: {letter_count}")  
  
        matching_templates = template_data.get(letter_count, [])  
  
        if not matching_templates:  
            logger.warning(f"[DEBUG] No templates found for length: {letter_count}")  
            return {"trick": "No matching templates for this input length."}  
  
        # Try multiple templates to find a match using all letters  
        max_attempts = 10  
        for attempt in range(max_attempts):  
            template = random.choice(matching_templates)  
            logger.info(f"[DEBUG] Attempt {attempt+1}: Trying Template: {template}")  
  
            placeholders = re.findall(r"\{(\w+)\}", template)  
            logger.info(f"[DEBUG] Detected Placeholders: {placeholders}")  
  
            if len(placeholders) != len(input_parts):  
                logger.info(f"[DEBUG] Skipping template due to placeholder count mismatch.")  
                continue  
  
            used_letters = []  
            words = {}  
            success = True  
  
            for placeholder, letter in zip(placeholders, input_parts):  
                base = placeholder.rstrip("s")  
                options = wordbank_cache.get(base + "s", {})  
                word_list = options.get(letter.upper(), [])  
  
                logger.debug(f"[DEBUG] Looking for placeholder '{placeholder}' with letter '{letter}' in category '{base}s'")  
  
                if not word_list:  
                    logger.warning(f"[WARNING] No match for placeholder '{placeholder}' and letter '{letter}'")  
                    success = False  
                    break  
  
                selected_word = random.choice(word_list)  
                words[placeholder] = selected_word  
                used_letters.append(letter)  
  
                logger.info(f"[✔️] Selected '{selected_word}' for placeholder '{placeholder}' and letter '{letter}'")  
  
            if success:  
                final_sentence = template  
                for key, val in words.items():  
                    final_sentence = final_sentence.replace(f"{{{key}}}", val, 1)  
  
                logger.info(f"[✅] Final sentence: {final_sentence}")  
                return {"trick": final_sentence}  
  
        logger.error(f"[❌] All {max_attempts} attempts failed to generate sentence using all letters.")  
        return {"trick": "Couldn't generate a sentence using all letters."}  
  
    return {"trick": "Invalid trick type selected."}
