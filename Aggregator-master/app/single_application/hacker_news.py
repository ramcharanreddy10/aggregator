from fastapi import APIRouter, HTTPException, FastAPI
from pydantic import BaseModel
import httpx
import uvicorn
import asyncio

# --- Configuration ---
BASE_URL = "https://hacker-news.firebaseio.com/v0"

# --- APIRouter Instance ---
router = APIRouter()

# --- Pydantic Models ---
class Story(BaseModel):
    id: int
    title: str = "N/A"
    url: str | None = None
    by: str = "N/A"
    score: int = 0
    time: int = 0
    type: str = "N/A"
    descendants: int = 0

class User(BaseModel):
    id: str
    created: int
    karma: int
    about: str | None = None
    submitted: list[int] = []

# --- Helper Functions ---
async def fetch_item(session: httpx.AsyncClient, item_id: int) -> dict | None:
    """Fetches a single item (story, comment, etc.) from the HN API."""
    url = f"{BASE_URL}/item/{item_id}.json"
    try:
        resp = await session.get(url)
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPStatusError, httpx.RequestError):
        return None # Return None on failure to handle gracefully in batch requests

async def fetch_user(user_id: str) -> dict:
    """Fetches a single user from the HN API."""
    url = f"{BASE_URL}/user/{user_id}.json"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            user_data = resp.json()
            if not user_data:
                raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
            return user_data
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Failed to fetch user: {e.response.text}")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Could not connect to the Hacker News API.")

# --- API Endpoints ---
async def get_stories_by_type(story_type: str):
    """Generic function to fetch top, new, or best stories."""
    url = f"{BASE_URL}/{story_type}stories.json"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            story_ids = resp.json()[:10]
            
            # Concurrently fetch details for all stories
            tasks = [fetch_item(client, story_id) for story_id in story_ids]
            results = await asyncio.gather(*tasks)
            
            # Filter out any failed requests and create Story models
            return [Story(**data) for data in results if data and data.get("type") == "story"]
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Failed to fetch {story_type} stories: {e.response.text}")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Could not connect to the Hacker News API.")

@router.get("/topstories", response_model=list[Story])
async def get_top_stories():
    """Fetches the top 10 stories from Hacker News."""
    return await get_stories_by_type("top")

@router.get("/newstories", response_model=list[Story])
async def get_new_stories():
    """Fetches the 10 newest stories from Hacker News."""
    return await get_stories_by_type("new")

@router.get("/item/{item_id}", response_model=Story)
async def get_story_item(item_id: int):
    """Fetches a single story by its item ID."""
    async with httpx.AsyncClient() as client:
        story_data = await fetch_item(client, item_id)
        if not story_data:
            raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found or failed to fetch.")
        return Story(**story_data)

@router.get("/user/{user_id}", response_model=User)
async def get_hn_user(user_id: str):
    """Fetches a Hacker News user by their ID."""
    user_data = await fetch_user(user_id)
    return User(**user_data)

# --- Standalone App ---
app = FastAPI(title="Standalone Hacker News API")
app.include_router(router, prefix="/hackernews", tags=["Hacker News"])

if __name__ == "__main__":
    uvicorn.run("hacker_news:app", host="127.0.0.1", port=8000, reload=True)

