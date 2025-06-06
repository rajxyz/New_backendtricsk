import wikipedia
import re

def fetch_abbreviation_details(term: str):
    # Normalize input (e.g. "w,h,o" -> "WHO")
    normalized = term.replace(",", "").replace(".", "").replace(" ", "").upper()
    print(f"[DEBUG] Normalized term: {normalized}")

    try:
        # Search Wikipedia using normalized term
        search_results = wikipedia.search(normalized)
        print(f"[DEBUG] Wikipedia search results for '{normalized}': {search_results}")

        if not search_results:
            return {
                "abbr": normalized,
                "full_form": "Not found",
                "description": "No summary found for this abbreviation."
            }

        # Use the first result as the full form
        full_form = search_results[0]
        print(f"[DEBUG] Using first search result as full form: {full_form}")

        # Get a short summary (first sentence only)
        summary = wikipedia.summary(full_form, sentences=1)
        print(f"[DEBUG] Summary fetched: {summary}")

        return {
            "abbr": normalized,
            "full_form": full_form,
            "description": summary
        }

    except wikipedia.DisambiguationError as e:
        print(f"[ERROR] Disambiguation error: {e.options[:5]}")
        return {
            "abbr": normalized,
            "full_form": "Ambiguous",
            "description": f"Ambiguous abbreviation. Possible meanings: {', '.join(e.options[:5])}"
        }

    except wikipedia.PageError:
        print(f"[ERROR] Page not found for: {normalized}")
        return {
            "abbr": normalized,
            "full_form": "Not found",
            "description": f"No Wikipedia page found for '{normalized}'."
        }

    except Exception as e:
        print(f"[ERROR] Unexpected error while fetching '{normalized}': {e}")
        return {
            "abbr": normalized,
            "full_form": "Error",
            "description": f"Unexpected error: {str(e)}"
        }
