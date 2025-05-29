from fastapi import APIRouter, Query
from utils import load_data

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/")
def search_items(category: str, query: str = Query(..., min_length=1)):
    """
    Kisi category (actors, cricketers, animals) me se kisi item ko search karega.
    Example: /search/?category=actors&query=Shah
    """
    try:
        data = load_data(f"{category}.json")
        results = [item for item in data if query.lower() in item.lower()]
        return {"category": category, "query": query, "results": results}
    except FileNotFoundError:
        return {"error": "Category not found"}
