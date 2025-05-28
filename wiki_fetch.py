from fastapi import APIRouter
from pydantic import BaseModel
from wikipedia import fetch_wikipedia_summary
from cache import save_to_cache

router = APIRouter()

class AbbrRequest(BaseModel):
    terms: list[str]

@router.post("/fetch-abbreviations/")
def fetch_abbreviations(request: AbbrRequest):
    results = []
    for term in request.terms:
        data = fetch_wikipedia_summary(term)
        if data:
            save_to_cache(data)  # ye tumhara json me auto-save karega
            results.append(data)
    return {"fetched": results}
