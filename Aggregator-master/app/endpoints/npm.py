from fastapi import APIRouter, HTTPException, FastAPI
from pydantic import BaseModel
import httpx
import uvicorn

# --- Configuration ---
BASE_URL = "https://registry.npmjs.org"

# --- APIRouter Instance ---
router = APIRouter()

# --- Pydantic Models ---
class NpmPackage(BaseModel):
    name: str
    description: str | None = None
    latest_version: str
    homepage: str | None = None

class NpmLatestVersion(BaseModel):
    package_name: str
    latest_version: str

# --- API Endpoints ---
@router.get("/{package_name}", response_model=NpmPackage)
async def fetch_npm_package(package_name: str):
    """Fetches comprehensive details for a specific npm package."""
    url = f"{BASE_URL}/{package_name}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Package '{package_name}' not found on npm.")
            raise HTTPException(status_code=exc.response.status_code, detail=f"Error fetching npm package: {exc.response.text}")
        except httpx.RequestError as exc:
             raise HTTPException(status_code=503, detail=f"Service unavailable: {exc}")

        data = resp.json()
        latest_version = data.get("dist-tags", {}).get("latest", "0.0.0")
        return NpmPackage(
            name=data.get("name", package_name),
            description=data.get("description", ""),
            latest_version=latest_version,
            homepage=data.get("homepage")
        )

@router.get("/{package_name}/latest", response_model=NpmLatestVersion)
async def fetch_npm_latest(package_name: str):
    """Fetches only the latest version for a specific npm package."""
    url = f"{BASE_URL}/{package_name}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Package '{package_name}' not found on npm.")
            raise HTTPException(status_code=exc.response.status_code, detail=f"Error fetching npm version: {exc.response.text}")
        except httpx.RequestError as exc:
             raise HTTPException(status_code=503, detail=f"Service unavailable: {exc}")

        data = resp.json()
        latest_version = data.get("dist-tags", {}).get("latest", "0.0.0")
        return NpmLatestVersion(
            package_name=data.get("name", package_name),
            latest_version=latest_version
        )

# --- Standalone App ---
app = FastAPI(title="Standalone npm API")
app.include_router(router, prefix="/npm", tags=["npm"])

if __name__ == "__main__":
    uvicorn.run("npm:app", host="127.0.0.1", port=8002, reload=True)
