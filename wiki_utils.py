import wikipedia
import re

def fetch_abbreviation_details(term: str):
    # Normalize input (e.g. "w,h,o" -> "WHO")
    normalized = term.replace(",", "").replace(".", "").replace(" ", "").upper()

    try:
        # Search Wikipedia using normalized term
        search_results = wikipedia.search(normalized)
        if not search_results:
            return {
                "abbr": normalized,
                "full_form": "Not found",
                "description": "No summary found for this abbreviation."
            }

        # Use the first result as the full form
        full_form = search_results[0]

        # Get a short summary (first sentence only)
        summary = wikipedia.summary(full_form, sentences=1)

        return {
            "abbr": normalized,
            "full_form": full_form,
            "description": summary
        }

    except Exception as e:
        return {
            "abbr": normalized,
            "full_form": "Error",
            "description": str(e)
        }
