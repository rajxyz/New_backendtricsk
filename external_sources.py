import requests

def fetch_from_duckduckgo(term: str):
    """
    Try to fetch a definition from DuckDuckGo's Instant Answer API.
    """
    try:
        response = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": term, "format": "json", "no_redirect": "1", "no_html": "1"},
            timeout=5
        )
        data = response.json()

        abstract = data.get("AbstractText", "")
        heading = data.get("Heading", "")

        if abstract:
            return {
                "abbr": term,
                "full_form": heading or term,
                "description": abstract
            }

        return None
    except Exception as e:
        print(f"[DuckDuckGo ERROR] {e}")
        return None


def fetch_from_abbreviations_com(term: str):
    """
    Fetch from Abbreviations.com via their unofficial API.
    This may break if they change their layout.
    """
    try:
        url = f"https://www.abbreviations.com/serp.php?st={term}&qtype=1"
        response = requests.get(url, timeout=5)
        if "meaning" in response.text.lower():
            # Naive string matching (optional: use BeautifulSoup if structure is fixed)
            lines = response.text.splitlines()
            for line in lines:
                if '<p class="desc">' in line:
                    desc = line.strip().replace('<p class="desc">', '').replace('</p>', '')
                    return {
                        "abbr": term,
                        "full_form": term,
                        "description": desc
                    }
        return None
    except Exception as e:
        print(f"[Abbreviations.com ERROR] {e}")
        return None
