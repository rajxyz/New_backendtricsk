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

    # Normalize wordbank keys to lowercase for flexible lookup
    normalized_wordbank = {k.lower(): v for k, v in wordbank.items()}

    for ph in placeholders:
        plural = False
        base_ph = ph

        # Detect plural placeholders like nouns, verbs, adjectives, adverbs
        if base_ph.endswith('s') and base_ph[:-1] in ['noun', 'verb', 'adjective', 'adverb']:
            plural = True
            base_ph = base_ph[:-1]

        base_key = base_ph.lower()
        plural_key = base_key + 's'

        # Determine which key to use in the wordbank (plural or singular)
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

        word_list = []
        if lookup_key:
            for letter in input_letters:
                letter_upper = letter.upper()
                letter_lower = letter.lower()

                # Try uppercase letter key, then lowercase letter key
                matched = normalized_wordbank[lookup_key].get(letter_upper) or normalized_wordbank[lookup_key].get(letter_lower) or []
                print(f"  Letter '{letter}' (upper: '{letter_upper}') => {matched}")
                word_list.extend(matched)
        else:
            print(f"[❌] No matching key found for placeholder '{ph}' in wordbank.")

        # Fallback words for some placeholders if no match found
        fallback_words = {
            "adverb": ["quickly", "silently", "boldly", "calmly", "gracefully"],
            "preposition": ["under", "over", "beside", "with", "without"],
            "noun": ["thing", "object", "item"],
            "verb": ["do", "make", "go"],
            "adjective": ["good", "nice", "happy"],
        }

        if not word_list:
            word = random.choice(fallback_words.get(base_ph, [f"<{ph}>"]))
            print(f"[❌] No match found for placeholder '{ph}' with letters {input_letters}. Using fallback: {word}")
        else:
            word = random.choice(word_list)
            if plural:
                word = p.plural(word)
            print(f"[✔️] Chosen word for '{ph}': {word}")

        # Replace both placeholder styles, one occurrence at a time
        template = template.replace(f"[{ph}]", word, 1)
        template = template.replace(f"{{{ph}}}", word, 1)

    if "<" in template and ">" in template:
        print("[⚠️ WARNING] Some placeholders may not have been replaced correctly.")

    print(f"✅ Final sentence: {template}")
    return template
