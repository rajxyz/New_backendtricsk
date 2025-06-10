import json
import random
import inflect
from pathlib import Path

p = inflect.engine()
BASE_DIR = Path(__file__).resolve().parent

def load_wordbank(filename="wordbank.json") -> dict:
    path = BASE_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_templates(filename="English-templates.json") -> list:
    path = BASE_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("TEMPLATES", [])

def extract_placeholders(template: str) -> list:
    placeholders = []

    # Detect [placeholder]
    start = 0
    while True:
        start = template.find('[', start)
        if start == -1:
            break
        end = template.find(']', start)
        if end == -1:
            break
        placeholders.append(template[start+1:end])
        start = end + 1

    # Detect {placeholder}
    start = 0
    while True:
        start = template.find('{', start)
        if start == -1:
            break
        end = template.find('}', start)
        if end == -1:
            break
        placeholders.append(template[start+1:end])
        start = end + 1

    return placeholders

def generate_template_sentence(template: str, wordbank: dict, input_letters: list) -> str:
    print("\n--- DEBUGGING TEMPLATE GENERATION ---")
    print(f"Original template: {template}")
    print(f"Input letters: {input_letters}")

    placeholders = extract_placeholders(template)
    print(f"Detected placeholders: {placeholders}")

    normalized_wordbank = {k.lower(): v for k, v in wordbank.items()}

    used_letters = set()

    for ph in placeholders:
        plural = False
        base_ph = ph

        if base_ph.endswith('s') and base_ph[:-1] in ['noun', 'verb', 'adjective', 'adverb']:
            plural = True
            base_ph = base_ph[:-1]

        base_key = base_ph.lower()
        plural_key = base_key + 's'

        if plural_key in normalized_wordbank:
            lookup_key = plural_key
        elif base_key in normalized_wordbank:
            lookup_key = base_key
        else:
            lookup_key = None

        print(f"\nHandling placeholder: {ph}")
        print(f"Base placeholder: {base_ph}")
        print(f"Plural: {plural}")
        print(f"Looking in wordbank key: {lookup_key}")

        selected_word = None

        if lookup_key:
            for letter in input_letters:
                if letter in used_letters:
                    continue

                letter_upper = letter.upper()
                letter_lower = letter.lower()

                matched = normalized_wordbank[lookup_key].get(letter_upper) or normalized_wordbank[lookup_key].get(letter_lower) or []
                if matched:
                    selected_word = random.choice(matched)
                    used_letters.add(letter)
                    print(f"[✔️] Selected word '{selected_word}' for letter '{letter}'")
                    break

        fallback_words = {
            "adverb": ["fast", "well", "soon", "boldly", "kindly"],
            "preposition": ["with", "without", "under", "over"],
            "noun": ["thing", "idea", "item", "goal"],
            "verb": ["go", "run", "do", "make"],
            "adjective": ["cool", "big", "smart", "fun"]
        }

        if not selected_word:
            selected_word = random.choice(fallback_words.get(base_ph, [f"<{ph}>"]))
            print(f"[❌] Using fallback word: {selected_word}")

        if plural:
            selected_word = p.plural(selected_word)

        template = template.replace(f"[{ph}]", selected_word, 1)
        template = template.replace(f"{{{ph}}}", selected_word, 1)

    print(f"✅ Final sentence: {template}")
    return template
