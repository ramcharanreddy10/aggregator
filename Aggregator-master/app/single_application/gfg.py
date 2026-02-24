from fastapi import APIRouter, HTTPException, FastAPI
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup
import uvicorn

# --- APIRouter Instance ---
router = APIRouter()

# --- Pydantic Models ---
class GFGStats(BaseModel):
    totalSolved: int | None = None
    easy: int | None = None
    medium: int | None = None
    hard: int | None = None

class GFGPOTD(BaseModel):
    title: str | None = "Not found"
    link: str | None = "Not found"

# --- API Endpoints ---
@router.get("/stats/{username}", response_model=GFGStats)
async def get_gfg_stats(username: str):
    """Fetches a user's problem-solving stats from a GFG stats API."""
    url = f"https://geeks-for-geeks-stats-api.vercel.app/?raw=y&userName={username}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            # The external API uses lowercase keys for stats
            return GFGStats(
                totalSolved=data.get("totalProblemsSolved"),
                easy=data.get("easy"),
                medium=data.get("medium"),
                hard=data.get("hard"),
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"GFG stats fetch failed for user '{username}'. The user may not exist.")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Could not connect to the GFG stats service.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.get("/potd", response_model=GFGPOTD)
async def get_gfg_potd():
    """Fetches and scrapes the Problem of the Day from the GFG website."""
    url = "https://www.geeksforgeeks.org/problem-of-the-day"
    # A user-agent header can help avoid being blocked
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Find the main container for the POTD to narrow the search
            potd_div = soup.find('div', class_=lambda x: x and 'POTD_header-main' in x)
            if potd_div:
                title_tag = potd_div.find('a', href=True)
                if title_tag:
                    title = title_tag.text.strip()
                    link = title_tag['href']
                    return GFGPOTD(title=title, link=link)
            
            return GFGPOTD(title="Could not parse POTD title/link from page", link=url)
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to fetch or parse the GFG POTD page.")

# --- Standalone App ---
app = FastAPI(title="Standalone GeeksForGeeks API")
app.include_router(router, prefix="/gfg", tags=["GeeksForGeeks"])

if __name__ == "__main__":
    uvicorn.run("gfg:app", host="127.0.0.1", port=8000, reload=True)

