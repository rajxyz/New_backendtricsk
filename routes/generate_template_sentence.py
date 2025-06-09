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

    for ph in placeholders:
        plural = False
        base_ph = ph

        if base_ph.endswith('s') and base_ph[:-1] in ['noun', 'verb', 'adjective', 'adverb']:
            plural = True
            base_ph = base_ph[:-1]

        json_key = (
            base_ph.capitalize() + 's'
            if base_ph in ['noun', 'verb', 'adjective', 'adverb']
            else base_ph
        )

        print(f"\nHandling placeholder: {ph}")
        print(f"Base placeholder: {base_ph}")
        print(f"Plural: {plural}")
        print(f"Looking in wordbank key: {json_key}")

        word_list = []
        for letter in input_letters:
            upper_letter = letter.upper()
            matched = wordbank.get(json_key, {}).get(upper_letter, [])
            print(f"  Letter '{upper_letter}' => {matched}")
            word_list.extend(matched)

        if word_list:
            word = random.choice(word_list)
            if plural:
                word = p.plural(word)
            print(f"[✔️] Chosen word for '{ph}': {word}")
        else:
            word = f"<{ph}>"
            print(f"[❌] No match found for placeholder '{ph}' with letters {input_letters}. Using fallback: {word}")

        # Replace both formats
        template = template.replace(f"[{ph}]", word, 1)
        template = template.replace(f"{{{ph}}}", word, 1)

    if "<" in template and ">" in template:
        print("[⚠️ WARNING] Some placeholders may not have been replaced correctly.")

    print(f"✅ Final sentence: {template}")
    return template
