from fastapi import APIRouter, HTTPException, FastAPI
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv
import uvicorn

# --- Configuration ---
load_dotenv()
BASE_URL = "https://api.github.com"
# IMPORTANT: Create a .env file in the same directory and add your GitHub Personal Access Token.
# Example: GITHUB_TOKEN=your_token_here
TOKEN = os.getenv("GITHUB_TOKEN")

# --- APIRouter Instance ---
router = APIRouter()

# --- Pydantic Models ---
class Repo(BaseModel):
    id: int
    name: str
    url: str

class Issue(BaseModel):
    id: int
    title: str
    url: str

# New model for Pull Requests
class PullRequest(BaseModel):
    id: int
    title: str
    url: str
    user: str

# --- Helper Function ---
def get_headers():
    """Validates the GitHub token and returns authorization headers."""
    if not TOKEN:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN not found. Please create a .env file with your token.")
    return {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}

# --- API Endpoints ---
@router.get("/repos", response_model=list[Repo])
async def fetch_repos():
    """Fetches the 10 most recently updated repositories for the authenticated user."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{BASE_URL}/user/repos?sort=updated&per_page=10", headers=get_headers())
            resp.raise_for_status()
            return [Repo(id=r['id'], name=r['name'], url=r['html_url']) for r in resp.json()]
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Failed to fetch GitHub repos: {e.response.text}")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Could not connect to the GitHub API.")

@router.get("/issues", response_model=list[Issue])
async def fetch_issues():
    """Fetches the 10 most recently updated issues assigned to the authenticated user."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{BASE_URL}/issues?filter=assigned&sort=updated&per_page=10", headers=get_headers())
            resp.raise_for_status()
            return [Issue(id=i['id'], title=i['title'], url=i['html_url']) for i in resp.json()]
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Failed to fetch GitHub issues: {e.response.text}")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Could not connect to the GitHub API.")

# --- New Endpoint for Pull Requests ---
@router.get("/repos/{owner}/{repo}/pulls", response_model=list[PullRequest], summary="List Pull Requests")
async def fetch_pull_requests(owner: str, repo: str):
    """Fetches open pull requests for a specific repository."""
    async with httpx.AsyncClient() as client:
        try:
            # By default, the GitHub API fetches open PRs.
            url = f"{BASE_URL}/repos/{owner}/{repo}/pulls"
            resp = await client.get(url, headers=get_headers())
            resp.raise_for_status()
            
            pull_requests = resp.json()
            return [
                PullRequest(
                    id=pr['id'],
                    title=pr['title'],
                    url=pr['html_url'],
                    user=pr['user']['login']
                ) for pr in pull_requests
            ]
        except httpx.HTTPStatusError as e:
            detail_msg = f"Failed to fetch pull requests for {owner}/{repo}: {e.response.text}"
            if e.response.status_code == 404:
                detail_msg = f"Repository {owner}/{repo} not found."
            raise HTTPException(status_code=e.response.status_code, detail=detail_msg)
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Could not connect to the GitHub API.")

# --- Main FastAPI App ---
app = FastAPI(
    title="GitHub Aggregator API",
    description="An API to fetch repositories, issues, and pull requests from GitHub.",
    version="1.0.0"
)
app.include_router(router, prefix="/github", tags=["GitHub"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the GitHub Aggregator API. Visit /docs for documentation."}

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: GITHUB_TOKEN is not set. Please create a .env file and add your GitHub Personal Access Token.")
        print("Example .env file content: GITHUB_TOKEN=ghp_...")
    else:
        # Note: The app is run with `main:app` to match the filename.
        uvicorn.run("github:app", host="127.0.0.1", port=8000, reload=True)
