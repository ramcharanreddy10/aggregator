from fastapi import APIRouter, HTTPException, FastAPI
from pydantic import BaseModel
import httpx
from datetime import datetime
import uvicorn
import os
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
BASE_URL = "https://codeforces.com/api"
DEFAULT_CODEFORCES_HANDLE = os.getenv("CODEFORCES_HANDLE", "")

# --- APIRouter Instance ---
router = APIRouter()

# --- Pydantic Models ---
class Contest(BaseModel):
    id: int
    name: str
    phase: str
    link: str

class UserInfo(BaseModel):
    handle: str
    firstName: str | None = None
    lastName: str | None = None
    country: str | None = None
    organization: str | None = None
    rating: int | None = None
    maxRating: int | None = None
    rank: str | None = None
    maxRank: str | None = None
    lastOnline: str | None = None
    profileLink: str

# --- Helper Function ---
def format_time(timestamp: int | None) -> str | None:
    if not timestamp:
        return None
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

# --- API Endpoints ---
@router.get("/contests", response_model=list[Contest], summary="Get upcoming contests")
async def get_contests():
    """Fetches the next 10 upcoming contests from Codeforces."""
    url = f"{BASE_URL}/contest.list"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            contests = resp.json()["result"]
            # Filter for upcoming contests and limit to 10
            upcoming = [Contest(**c, link=f"https://codeforces.com/contest/{c['id']}") for c in contests if c.get('phase') == 'BEFORE']
            return upcoming[:10]
        except (httpx.HTTPStatusError, KeyError) as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch or parse contests: {e}")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Could not connect to the Codeforces API.")

@router.get("/userinfo/me", response_model=UserInfo, summary="Get info for the default user")
async def get_default_user_info():
    """
    Fetches user info for the handle specified in the CODEFORCES_HANDLE .env variable.
    """
    if not DEFAULT_CODEFORCES_HANDLE:
        raise HTTPException(
            status_code=400,
            detail="CODEFORCES_HANDLE is not set in the environment file."
        )
    
    handle = DEFAULT_CODEFORCES_HANDLE
    url = f"{BASE_URL}/user.info?handles={handle}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            user_data = resp.json()["result"][0]
            return UserInfo(
                **user_data,
                lastOnline=format_time(user_data.get("lastOnlineTimeSeconds")),
                profileLink=f"https://codeforces.com/profile/{user_data['handle']}"
            )
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=404, detail=f"Default Codeforces user '{handle}' not found or API error.")
        except (KeyError, IndexError):
            raise HTTPException(status_code=404, detail=f"Default Codeforces user '{handle}' not found.")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Could not connect to the Codeforces API.")

@router.get("/userinfo/{handle}", response_model=UserInfo, summary="Get info for a specific user")
async def get_user_info(handle: str):
    """Fetches user info for a specific Codeforces handle."""
    url = f"{BASE_URL}/user.info?handles={handle}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            # The API returns a list, even for a single user
            user_data = resp.json()["result"][0]
            return UserInfo(
                **user_data,
                lastOnline=format_time(user_data.get("lastOnlineTimeSeconds")),
                profileLink=f"https://codeforces.com/profile/{user_data['handle']}"
            )
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=404, detail=f"Codeforces user '{handle}' not found or API error.")
        except (KeyError, IndexError):
            raise HTTPException(status_code=404, detail=f"Codeforces user '{handle}' not found.")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Could not connect to the Codeforces API.")

# --- Standalone App ---
app = FastAPI(title="Standalone Codeforces API")
app.include_router(router, prefix="/codeforces", tags=["Codeforces"])

if __name__ == "__main__":
    uvicorn.run("codeforces:app", host="127.0.0.1", port=8000, reload=True)
