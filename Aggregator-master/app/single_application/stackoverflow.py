from fastapi import APIRouter, HTTPException, FastAPI, Query
from pydantic import BaseModel, Field
import httpx
import os
from dotenv import load_dotenv
import uvicorn
from datetime import datetime

# --- Configuration ---
load_dotenv()
BASE_URL = "https://api.stackexchange.com/2.3"
DEFAULT_USER_ID = os.getenv("STACKOVERFLOW_USER_ID")
DEFAULT_USERNAME = os.getenv("STACKOVERFLOW_USERNAME")

# --- APIRouter Instance ---
router = APIRouter()

# --- Pydantic Models ---
class Question(BaseModel):
    question_id: int
    title: str
    link: str

class Answer(BaseModel):
    answer_id: int
    question_id: int
    link: str

class TimelineEvent(BaseModel):
    timeline_type: str
    creation_date: str
    detail: str | None = None
    link: str

# NEW: Model for a single featured question
class FeaturedQuestion(BaseModel):
    title: str
    link: str
    bounty_amount: int = Field(..., description="The reputation bounty offered for the question.")
    answer_count: int
    owner_display_name: str
    
# --- Helper Functions ---
async def get_user_id_from_username(client: httpx.AsyncClient, username: str) -> int:
    """Finds a user's ID based on their display name."""
    url = f"{BASE_URL}/users?order=desc&sort=reputation&inname={username}&site=stackoverflow"
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if not items:
            raise HTTPException(status_code=404, detail=f"Stack Overflow user '{username}' not found")
        return items[0]["user_id"]
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Failed to fetch user ID.")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Could not connect to the Stack Exchange API.")


async def resolve_user_id(client: httpx.AsyncClient, user_id: int | None = None, username: str | None = None) -> int:
    """Gets a user ID from arguments or falls back to .env variables."""
    if user_id:
        return user_id
    if DEFAULT_USER_ID:
        return int(DEFAULT_USER_ID)
    if username:
        return await get_user_id_from_username(client, username)
    if DEFAULT_USERNAME:
        return await get_user_id_from_username(client, DEFAULT_USERNAME)
    raise HTTPException(status_code=400, detail="A Stack Overflow user_id or username must be provided.")

# --- API Endpoints ---
@router.get("/featured", response_model=list[FeaturedQuestion], summary="Get featured (bountied) questions")
async def fetch_featured_questions():
    """
    Fetches the 15 most recent questions with an active bounty, similar to the
    'Interesting posts' section on the homepage.
    """
    url = f"{BASE_URL}/questions/featured?order=desc&sort=activity&site=stackoverflow"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json().get("items", [])
            return [
                FeaturedQuestion(
                    title=item.get("title"),
                    link=item.get("link"),
                    bounty_amount=item.get("bounty_amount"),
                    answer_count=item.get("answer_count"),
                    owner_display_name=item.get("owner", {}).get("display_name")
                )
                for item in data[:15]
            ]
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="Failed to fetch featured questions.")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Could not connect to the Stack Exchange API.")


@router.get("/questions", response_model=list[Question], summary="Get user's questions")
async def fetch_questions(
    user_id: int = Query(None, description="StackOverflow user ID"),
    username: str = Query(None, description="StackOverflow username")
):
    """Fetches the 10 most recent questions asked by a user."""
    async with httpx.AsyncClient() as client:
        resolved_user_id = await resolve_user_id(client, user_id, username)
        url = f"{BASE_URL}/users/{resolved_user_id}/questions?order=desc&sort=creation&site=stackoverflow"
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json().get("items", [])
            return [Question(**q) for q in data[:10]]
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="Failed to fetch questions.")

@router.get("/answers", response_model=list[Answer], summary="Get user's answers")
async def fetch_answers(
    user_id: int = Query(None, description="StackOverflow user ID"),
    username: str = Query(None, description="StackOverflow username")
):
    """Fetches the 10 most recent answers posted by a user."""
    async with httpx.AsyncClient() as client:
        resolved_user_id = await resolve_user_id(client, user_id, username)
        url = f"{BASE_URL}/users/{resolved_user_id}/answers?order=desc&sort=creation&site=stackoverflow"
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json().get("items", [])
            return [Answer(**a, link=f"https://stackoverflow.com/a/{a['answer_id']}") for a in data[:10]]
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="Failed to fetch answers.")

# --- Standalone App ---
app = FastAPI(title="Standalone StackOverflow API")
app.include_router(router, prefix="/stackoverflow", tags=["StackOverflow"])

if __name__ == "__main__":
    uvicorn.run("stackoverflow:app", host="127.0.0.1", port=8000, reload=True)

