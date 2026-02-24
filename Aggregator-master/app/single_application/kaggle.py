from fastapi import APIRouter, HTTPException, FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import uvicorn
import httpx

# --- Configuration ---
load_dotenv()
KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME", "")
KAGGLE_KEY = os.getenv("KAGGLE_KEY", "")
BASE_URL = "https://www.kaggle.com/api/v1"

# --- APIRouter Instance ---
router = APIRouter()

# --- Pydantic Models ---
class Dataset(BaseModel):
    title: str
    ref: str
    url: str

class Competition(BaseModel):
    ref: str
    title: str
    deadline: str

# --- Helper Function ---
def get_kaggle_auth():
    """Validates Kaggle credentials and returns them for Basic Authentication."""
    if not KAGGLE_USERNAME or not KAGGLE_KEY:
        raise HTTPException(status_code=500, detail="KAGGLE_USERNAME or KAGGLE_KEY not found in .env file.")
    return (KAGGLE_USERNAME, KAGGLE_KEY)

# --- API Endpoints ---
@router.get("/datasets", response_model=list[Dataset])
async def fetch_datasets():
    """Fetches the 10 most recently updated datasets from Kaggle via HTTP API."""
    auth = get_kaggle_auth()
    url = f"{BASE_URL}/datasets/list"
    params = {"sort_by": "updated", "page_size": 10}
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, auth=auth, params=params)
            resp.raise_for_status()
            datasets = resp.json()
            return [
                Dataset(title=d['title'], ref=d['ref'], url=f"https://www.kaggle.com/datasets/{d['ref']}")
                for d in datasets
            ]
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Failed to fetch Kaggle datasets: {e.response.text}")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Could not connect to the Kaggle API.")

@router.get("/competitions", response_model=list[Competition])
async def fetch_competitions():
    """Fetches the 10 most recent competitions from Kaggle via HTTP API."""
    auth = get_kaggle_auth()
    url = f"{BASE_URL}/competitions/list"
    params = {"sort_by": "latestDeadline", "page_size": 10}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, auth=auth, params=params)
            resp.raise_for_status()
            competitions = resp.json()
            return [
                Competition(ref=c['ref'], title=c['title'], deadline=c['deadline'])
                for c in competitions
            ]
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Failed to fetch Kaggle competitions: {e.response.text}")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Could not connect to the Kaggle API.")

# --- Standalone App ---
app = FastAPI(title="Standalone Kaggle API")
app.include_router(router, prefix="/kaggle", tags=["Kaggle"])

if __name__ == "__main__":
    uvicorn.run("kaggle:app", host="127.0.0.1", port=8000, reload=True)

