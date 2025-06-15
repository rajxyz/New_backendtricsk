import wikipedia
import re
from external_sources import fetch_from_duckduckgo, fetch_from_abbreviations_com

FALLBACK_SOURCES = [
    "wikipedia",
    "duckduckgo",
    "abbreviations_com",
]

# Common stopwords to skip while matching letters
STOPWORDS = {"is", "a", "an", "the", "of", "in", "on", "and", "to", "for", "as", "with", "by", "at", "from"}

# Phrases that often introduce a definition
DEFINITION_PATTERNS = [
    r"{abbr} (is|was|refers to|stands for|means|, short for)",
    r"The acronym {abbr} (is|was|means|stands for)"
]

def extract_full_form_from_text(abbr: str, text: str) -> str:
    abbr_upper = abbr.upper()
    abbr_letters = list(abbr_upper)

    for pattern in DEFINITION_PATTERNS:
        regex = re.compile(pattern.format(abbr=re.escape(abbr_upper)), re.IGNORECASE)
        match = regex.search(text)
        if match:
            start_idx = match.end()
            trailing_text = text[start_idx:]

            # Extract next 10 words after the definition pattern
            words = re.findall(r'\b\w+\b', trailing_text)
            cleaned_words = [w for w in words if w.lower() not in STOPWORDS]

            if len(cleaned_words) >= len(abbr_letters):
                match_letters = cleaned_words[:len(abbr_letters)]
                if all(w[0].upper() == abbr_letters[i] for i, w in enumerate(match_letters)):
                    return ' '.join(match_letters)
    return None

def fetch_abbreviation_details(term: str):
    normalized = term.replace(",", "").replace(".", "").replace(" ", "").upper()
    print(f"[DEBUG] Normalized term: {normalized}")

    for source in FALLBACK_SOURCES:
        try:
            if source == "wikipedia":
                result = fetch_from_wikipedia(normalized)
            elif source == "duckduckgo":
                result = fetch_from_duckduckgo(normalized)
            elif source == "abbreviations_com":
                result = fetch_from_abbreviations_com(normalized)
            else:
                continue

            if result and result.get("full_form") != "Not found":
                print(f"[DEBUG] Fetched from {source}")
                return result

        except Exception as e:
            print(f"[ERROR] {source} failed for {normalized}: {e}")

    return {
        "abbr": normalized,
        "full_form": "Not found",
        "description": "No definition found from available sources."
    }

def fetch_from_wikipedia(term: str):
    try:
        search_results = wikipedia.search(term)
        if not search_results:
            return None

        for result in search_results[:5]:
            try:
                summary = wikipedia.summary(result, sentences=2)

                full_form = extract_full_form_from_text(term, summary)
                if full_form:
                    return {
                        "abbr": term,
                        "full_form": full_form,
                        "description": summary
                    }

            except Exception:
                continue

        return None

    except wikipedia.DisambiguationError as e:
        return {
            "abbr": term,
            "full_form": "Ambiguous",
            "description": f"Ambiguous abbreviation. Possible meanings: {', '.join(e.options[:5])}"
        }
    except wikipedia.PageError:
        return None
    except Exception as e:
        raise e
            
