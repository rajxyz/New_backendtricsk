from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from wiki_utils import fetch_abbreviation_details  # Use updated function

router = APIRouter()

class WikiRequest(BaseModel):
    terms: List[str]

@router.post("/wiki")
async def get_abbreviation_info(request: WikiRequest):
    results = {}
    for term in request.terms:
        details = fetch_abbreviation_details(term)
        results[term] = details
    return results
