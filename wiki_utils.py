import wikipedia
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

def fetch_from_wikipedia(term: str):
    try:
        search_results = wikipedia.search(term)
        if not search_results:
            return None

        best_match = None
        best_score = -1

        for result in search_results[:10]:  # Limit to top 10 results for performance
            title = result.lower()
            score = 0

            if all(c.lower() in title for c in term.lower()):
                score += 2

            if any(keyword in title for keyword in PREFERRED_KEYWORDS):
                score += 3

            if score > best_score:
                best_score = score
                best_match = result

        if best_match:
            summary = wikipedia.summary(best_match, sentences=1)
            return {
                "abbr": term,
                "full_form": best_match,
                "description": summary
            }

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
