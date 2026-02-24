from fastapi import APIRouter, HTTPException, FastAPI, Query
from pydantic import BaseModel
import httpx
import uvicorn

# --- Configuration ---
BASE_URL = "http://hn.algolia.com/api/v1"

# --- APIRouter Instance ---
router = APIRouter()

# --- Pydantic Models ---
class Story(BaseModel):
    objectID: str
    title: str
    url: str | None = None
    points: int
    author: str

# --- API Endpoints ---
@router.get("/search", response_model=list[Story])
async def search_hacker_news(query: str = Query(..., min_length=1, description="The search term for stories.")):
    """Searches Hacker News for stories matching a query."""
    url = f"{BASE_URL}/search"
    params = {"query": query, "tags": "story"}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=f"Error searching Hacker News: {exc.response.text}")
        except httpx.RequestError as exc:
             raise HTTPException(status_code=503, detail=f"Service unavailable: {exc}")

        results = resp.json().get("hits", [])
        return [
            Story(
                objectID=hit.get("objectID"),
                title=hit.get("title", "No Title"),
                url=hit.get("url"),
                points=hit.get("points", 0),
                author=hit.get("author", "No Author")
            )
            for hit in results if hit.get("title") # Filter out empty items
        ]

# --- Standalone App ---
app = FastAPI(title="Standalone Hacker News API")
app.include_router(router, prefix="/hackernews", tags=["Hacker News"])

if __name__ == "__main__":
    uvicorn.run("hn:app", host="127.0.0.1", port=8004, reload=True)
