import wikipedia
from external_sources import fetch_from_duckduckgo, fetch_from_abbreviations_com
import re

FALLBACK_SOURCES = [
    "wikipedia",
    "duckduckgo",
    "abbreviations_com",
]

# Optional: You can update preferred keywords if needed
PREFERRED_KEYWORDS = [
    "company", "corporation", "organization", "institute", "agency",
    "authority", "committee", "commission", "center"
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


def fetch_from_wikipedia(term: str):
    try:
        search_results = wikipedia.search(term)
        if not search_results:
            return None

        for result in search_results[:5]:
            try:
                summary = wikipedia.summary(result, sentences=2)

                # ✅ Try extracting full form from the summary
                full_form = extract_full_form_from_text(term, summary)
                if full_form:
                    return {
                        "abbr": term,
                        "full_form": full_form,
                        "description": summary
                    }

            except Exception:
                continue

        # ❌ No valid full form found
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


def extract_full_form_from_text(abbr: str, text: str) -> str:
    """
    Try to intelligently extract a full form of abbreviation from Wikipedia summary.
    Looks for capital words matching the abbreviation letters.
    """
    words = re.findall(r'\b[A-Z][a-z]+\b', text)
    if not words or len(words) < len(abbr):
        return None

    candidates = []
    abbr = abbr.upper()

    for i in range(len(words) - len(abbr) + 1):
        chunk = words[i:i + len(abbr)]
        initials = ''.join([w[0].upper() for w in chunk])
        if initials == abbr:
            candidates.append(' '.join(chunk))

    return candidates[0] if candidates else None
