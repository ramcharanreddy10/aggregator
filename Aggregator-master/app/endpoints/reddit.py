from fastapi import APIRouter, HTTPException, FastAPI, Query
from pydantic import BaseModel
import httpx
import uvicorn

# --- Configuration ---
BASE_URL = "https://www.reddit.com"

# --- APIRouter Instance ---
router = APIRouter()

# --- Pydantic Models ---
class Post(BaseModel):
    id: str
    title: str
    subreddit: str
    url: str
    author: str
    score: int

# --- API Endpoints ---
@router.get("/r/{subreddit}/search", response_model=list[Post])
async def search_subreddit(
    subreddit: str,
    query: str = Query(..., min_length=1, description="The search term for posts.")
):
    """Searches a specific subreddit for posts matching a query."""
    url = f"{BASE_URL}/r/{subreddit}/search.json"
    # Reddit API requires a unique User-Agent
    headers = {"User-Agent": "FastAPI-Aggregator/0.1 by YourUsername"}
    params = {"q": query, "restrict_sr": "on", "limit": 25}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=f"Error searching Reddit: {exc.response.text}")
        except httpx.RequestError as exc:
             raise HTTPException(status_code=503, detail=f"Service unavailable: {exc}")

        results = resp.json().get("data", {}).get("children", [])
        return [
            Post(
                id=p["data"].get("id"),
                title=p["data"].get("title", "No Title"),
                subreddit=p["data"].get("subreddit", subreddit),
                url=f"{BASE_URL}{p['data'].get('permalink', '')}",
                author=p["data"].get("author", "No Author"),
                score=p["data"].get("score", 0)
            )
            for p in results
        ]

# --- Standalone App ---
app = FastAPI(title="Standalone Reddit API")
app.include_router(router, prefix="/reddit", tags=["Reddit"])

if __name__ == "__main__":
    uvicorn.run("reddit:app", host="127.0.0.1", port=8005, reload=True)
