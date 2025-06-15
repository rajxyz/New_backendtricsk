import wikipedia
import re
from external_sources import fetch_from_duckduckgo, fetch_from_abbreviations_com

FALLBACK_SOURCES = [
    "wikipedia",
    "duckduckgo",
    "abbreviations_com",
]

PREFERRED_KEYWORDS = [
    "company", "corporation", "organization", "institute", "agency", "authority", "committee", "commission", "center"
]

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

def extract_full_form_from_text(abbr: str, text: str) -> str:
    # Example: "SSTM stands for Super Sonic Transport Mission."
    pattern = re.compile(rf"\b{abbr}\b\s+(stands for|means|is short for|refers to)\s+(.*?)[\.\,\n]", re.IGNORECASE)
    match = pattern.search(text)
    if match:
        return match.group(2).strip()
    return ""

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

                # Fallback: use title as full_form if it contains all term letters
                if all(c.lower() in result.lower() for c in term.lower()):
                    return {
                        "abbr": term,
                        "full_form": result,
                        "description": summary
                    }
            except Exception as inner_e:
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
