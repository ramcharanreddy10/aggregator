from fastapi import APIRouter, HTTPException, FastAPI, Query
from pydantic import BaseModel, Field
import httpx
import uvicorn
from typing import List

# --- Configuration ---
BASE_URL = "https://api.stackexchange.com/2.3"

# --- APIRouter Instance ---
router = APIRouter()

# --- Pydantic Models ---
class Owner(BaseModel):
    display_name: str

class Question(BaseModel):
    question_id: int
    title: str
    link: str
    owner: Owner
    tags: List[str]
    score: int
    is_answered: bool

class SearchResponse(BaseModel):
    items: List[Question]

# --- API Endpoints ---
@router.get("/search", response_model=List[Question])
async def search_stackoverflow(
    query: str = Query(..., alias="q", description="The search query."),
    tagged: str = Query(..., description="Semicolon-delimited list of tags (e.g., 'python;pandas').")
):
    """Searches Stack Overflow for questions with specific tags."""
    url = f"{BASE_URL}/search"
    params = {
        "site": "stackoverflow",
        "intitle": query,
        "tagged": tagged,
        "sort": "relevance",
        "order": "desc"
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=f"Error searching Stack Overflow: {exc.response.text}")
        except httpx.RequestError as exc:
             raise HTTPException(status_code=503, detail=f"Service unavailable: {exc}")

        # Pydantic will automatically parse the 'items' from the response
        data = SearchResponse(**resp.json())
        return data.items

# --- Standalone App ---
app = FastAPI(title="Standalone Stack Overflow API")
app.include_router(router, prefix="/stackoverflow", tags=["Stack Overflow"])

if __name__ == "__main__":
    uvicorn.run("so:app", host="127.0.0.1", port=8006, reload=True)
