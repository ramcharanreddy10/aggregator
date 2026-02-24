from fastapi import APIRouter, HTTPException, FastAPI
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv
import uvicorn

# --- Configuration ---
load_dotenv()
BASE_URL = "https://dev.to/api"
API_KEY = os.getenv("DEVTO_API_KEY")

# --- APIRouter Instance ---
# This is the object the main aggregator app will import.
router = APIRouter()

# --- Pydantic Model ---
class Article(BaseModel):
    id: int
    title: str
    url: str
    author: str | None = None
    tags: str | None = None

# --- Helper Function ---
def get_headers():
    """Validates API key and returns request headers."""
    if not API_KEY:
        raise HTTPException(status_code=500, detail="DEVTO_API_KEY not found in .env file.")
    return {"api-key": API_KEY, "Accept": "application/vnd.forem.api-v1+json"}

# --- API Endpoints ---
@router.get("/articles", response_model=list[Article])
async def fetch_articles():
    """Fetches the latest 10 articles from DEV.to."""
    url = f"{BASE_URL}/articles/latest"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=get_headers(), params={"per_page": 10})
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=f"Error fetching articles: {exc.response.text}")
        except httpx.RequestError as exc:
             raise HTTPException(status_code=503, detail=f"Service unavailable: {exc}")

        articles = resp.json()
        return [
            Article(
                id=a["id"],
                title=a.get("title", "No Title"),
                url=a.get("url", ""),
                author=a.get("user", {}).get("name"),
                tags=", ".join(a.get("tag_list", [])) if isinstance(a.get("tag_list", []), list) else ""
            )
            for a in articles
        ]

@router.get("/article/{article_id}", response_model=Article)
async def fetch_single_article(article_id: int):
    """Fetches a single article by its ID from DEV.to."""
    url = f"{BASE_URL}/articles/{article_id}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=get_headers())
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Article with ID {article_id} not found.")
            raise HTTPException(status_code=exc.response.status_code, detail=f"Error fetching article: {exc.response.text}")
        except httpx.RequestError as exc:
             raise HTTPException(status_code=503, detail=f"Service unavailable: {exc}")

        a = resp.json()
        return Article(
            id=a["id"],
            title=a.get("title", "No Title"),
            url=a.get("url", ""),
            author=a.get("user", {}).get("name"),
            tags=", ".join(a.get("tag_list", [])) if isinstance(a.get("tag_list", []), list) else ""
        )

# --- Standalone App ---
# This app instance is for running the file directly and can be found by Uvicorn.
app = FastAPI(title="Standalone DEV.to API")
app.include_router(router, prefix="/devto", tags=["Dev.to"])

# This block will only run when you execute `python single_application/devto.py`
if __name__ == "__main__":
    uvicorn.run("devto:app", host="127.0.0.1", port=8000, reload=True)
