from fastapi import APIRouter, HTTPException, FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import uvicorn
import httpx
import asyncio

# --- Configuration ---
load_dotenv()
GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab.com")
TOKEN = os.getenv("GITLAB_TOKEN", "")
BASE_URL = f"{GITLAB_URL}/api/v4"

# --- APIRouter Instance ---
router = APIRouter()

# --- Pydantic Models ---
class Project(BaseModel):
    id: int
    name: str
    url: str

class Issue(BaseModel):
    id: int
    title: str
    url: str

class Pipeline(BaseModel):
    project: str
    pipeline_id: int
    status: str
    url: str

# --- Helper Function ---
def get_gitlab_headers():
    """Validates GitLab token and returns request headers."""
    if not TOKEN:
        raise HTTPException(status_code=500, detail="GITLAB_TOKEN not found in .env file.")
    return {"PRIVATE-TOKEN": TOKEN}

# --- API Endpoints ---
@router.get("/projects", response_model=list[Project])
async def fetch_projects():
    """Fetches the 10 most recent projects owned by the user."""
    headers = get_gitlab_headers()
    url = f"{BASE_URL}/projects"
    params = {"owned": "true", "order_by": "created_at", "sort": "desc", "per_page": 10}
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            projects = resp.json()
            return [Project(id=p['id'], name=p['name'], url=p['web_url']) for p in projects]
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Failed to fetch GitLab projects: {e.response.text}")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Could not connect to the GitLab API.")

@router.get("/issues", response_model=list[Issue])
async def fetch_issues():
    """Fetches the 10 most recently created issues assigned to the user."""
    headers = get_gitlab_headers()
    url = f"{BASE_URL}/issues"
    params = {"scope": "assigned_to_me", "order_by": "created_at", "sort": "desc", "per_page": 10}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            issues = resp.json()
            return [Issue(id=i['id'], title=i['title'], url=i['web_url']) for i in issues]
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Failed to fetch GitLab issues: {e.response.text}")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Could not connect to the GitLab API.")

async def get_pipelines_for_project(client: httpx.AsyncClient, project: dict, headers: dict):
    """Helper to fetch pipelines for a single project."""
    project_id = project['id']
    project_name = project['name']
    url = f"{BASE_URL}/projects/{project_id}/pipelines"
    params = {"per_page": 3}
    try:
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        pipelines = resp.json()
        return [Pipeline(project=project_name, pipeline_id=p['id'], status=p['status'], url=p['web_url']) for p in pipelines]
    except (httpx.HTTPStatusError, httpx.RequestError):
        return [] # Return empty list on failure for this project

@router.get("/pipelines", response_model=list[Pipeline])
async def fetch_pipelines():
    """Fetches recent pipelines from the user's top 3 projects."""
    headers = get_gitlab_headers()
    projects_url = f"{BASE_URL}/projects"
    project_params = {"owned": "true", "order_by": "last_activity_at", "sort": "desc", "per_page": 3}
    
    async with httpx.AsyncClient() as client:
        try:
            # First, get the most recent projects
            project_resp = await client.get(projects_url, headers=headers, params=project_params)
            project_resp.raise_for_status()
            projects = project_resp.json()

            # Concurrently fetch pipelines for those projects
            tasks = [get_pipelines_for_project(client, p, headers) for p in projects]
            results = await asyncio.gather(*tasks)
            
            # Flatten the list of lists into a single list
            return [pipeline for sublist in results for pipeline in sublist]
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Failed to fetch initial projects for pipelines: {e.response.text}")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Could not connect to the GitLab API.")


# --- Standalone App ---
app = FastAPI(title="Standalone GitLab API")
app.include_router(router, prefix="/gitlab", tags=["GitLab"])

if __name__ == "__main__":
    uvicorn.run("gitlab:app", host="127.0.0.1", port=8000, reload=True)

