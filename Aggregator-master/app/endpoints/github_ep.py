from fastapi import APIRouter, HTTPException, FastAPI
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv
import uvicorn

# --- Configuration ---
load_dotenv()
BASE_URL = "https://api.github.com"
API_TOKEN = os.getenv("GITHUB_API_TOKEN")

# --- APIRouter Instance ---
router = APIRouter()

# --- Pydantic Models ---
class Release(BaseModel):
    tag_name: str
    name: str | None = None
    url: str
    published_at: str

# --- Helper Function ---
def get_headers():
    """Returns request headers. A token is recommended for higher rate limits."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    return headers

# --- API Endpoints ---
@router.get("/{owner}/{repo}/releases", response_model=list[Release])
async def fetch_releases(owner: str, repo: str):
    """Fetches the latest 30 releases for a GitHub repository."""
    url = f"{BASE_URL}/repos/{owner}/{repo}/releases"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=get_headers())
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Repository '{owner}/{repo}' not found.")
            raise HTTPException(status_code=exc.response.status_code, detail=f"Error fetching releases: {exc.response.text}")
        except httpx.RequestError as exc:
             raise HTTPException(status_code=503, detail=f"Service unavailable: {exc}")

        releases = resp.json()
        return [
            Release(
                tag_name=r.get("tag_name", "No Tag"),
                name=r.get("name", "No Name"),
                url=r.get("html_url", ""),
                published_at=r.get("published_at", "")
            )
            for r in releases
        ]

# --- Standalone App ---
app = FastAPI(title="Standalone GitHub API")
app.include_router(router, prefix="/github", tags=["GitHub"])

if __name__ == "__main__":
    uvicorn.run("github_ep:app", host="127.0.0.1", port=8003, reload=True)
