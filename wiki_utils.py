import wikipedia
from external_sources import fetch_from_duckduckgo, fetch_from_abbreviations_com

# You can adjust the order of sources dynamically here
FALLBACK_SOURCES = [
    "wikipedia",
    "duckduckgo",
    "abbreviations_com",
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

    # Fallback if all sources fail
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
        full_form = search_results[0]
        summary = wikipedia.summary(full_form, sentences=1)
        return {
            "abbr": term,
            "full_form": full_form,
            "description": summary
        }
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
