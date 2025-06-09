import wikipedia
import re

def clean_summary(text):
    # Remove parenthesis and brackets for clarity
    text = re.sub(r'\s*[^)]*', '', text)
    text = re.sub(r'\s*[^]]*', '', text)

    # Truncate to the first sentence
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return sentences[0] if sentences else text.strip()

def fetch_abbreviation_details(term: str):
    normalized = term.replace(",", "").replace(".", "").replace(" ", "").upper()
    print(f"[DEBUG] Normalized term: {normalized}")

    try:
        search_results = wikipedia.search(normalized)
        print(f"[DEBUG] Wikipedia search results for '{normalized}': {search_results}")

        if not search_results:
            return {
                "abbr": normalized,
                "full_form": "Not found",
                "description": "No summary found for this abbreviation."
            }

        full_form = search_results[0]
        print(f"[DEBUG] Using first search result as full form: {full_form}")

        raw_summary = wikipedia.summary(full_form, sentences=2)
        cleaned_summary = clean_summary(raw_summary)
        print(f"[DEBUG] Cleaned summary: {cleaned_summary}")

        return {
            "abbr": normalized,
            "full_form": full_form,
            "description": cleaned_summary
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
