from fastapi import APIRouter, HTTPException, FastAPI
from pydantic import BaseModel, Field
import httpx
import uvicorn

# --- Configuration ---
BASE_URL = "https://pypi.org/pypi"

# --- APIRouter Instance ---
router = APIRouter()

# --- Pydantic Models ---
class PackageInfo(BaseModel):
    name: str
    version: str
    summary: str
    author: str | None = None
    home_page: str | None = Field(None, alias="home_page")

class LatestVersion(BaseModel):
    package_name: str
    latest_version: str

# --- API Endpoints ---
@router.get("/{package_name}", response_model=PackageInfo)
async def fetch_package_details(package_name: str):
    """Fetches comprehensive details for a specific Python package."""
    url = f"{BASE_URL}/{package_name}/json"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Package '{package_name}' not found on PyPI.")
            raise HTTPException(status_code=exc.response.status_code, detail=f"Error fetching package details: {exc.response.text}")
        except httpx.RequestError as exc:
             raise HTTPException(status_code=503, detail=f"Service unavailable: {exc}")

        data = resp.json()["info"]
        return PackageInfo(
            name=data.get("name", "No Name"),
            version=data.get("version", "0.0.0"),
            summary=data.get("summary", ""),
            author=data.get("author"),
            home_page=data.get("home_page")
        )

@router.get("/{package_name}/latest", response_model=LatestVersion)
async def fetch_latest_version(package_name: str):
    """Fetches only the latest version number for a specific Python package."""
    url = f"{BASE_URL}/{package_name}/json"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Package '{package_name}' not found on PyPI.")
            raise HTTPException(status_code=exc.response.status_code, detail=f"Error fetching package version: {exc.response.text}")
        except httpx.RequestError as exc:
             raise HTTPException(status_code=503, detail=f"Service unavailable: {exc}")

        data = resp.json()["info"]
        return LatestVersion(
            package_name=data.get("name", package_name),
            latest_version=data.get("version", "0.0.0")
        )

# --- Standalone App ---
app = FastAPI(title="Standalone PyPI API")
app.include_router(router, prefix="/pypi", tags=["PyPI"])

if __name__ == "__main__":
    uvicorn.run("pypi:app", host="127.0.0.1", port=8001, reload=True)
