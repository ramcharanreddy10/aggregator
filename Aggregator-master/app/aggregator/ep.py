from fastapi import FastAPI
import uvicorn
import sys
import os

# Add the parent directory to the Python path to find the 'endpoints' module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the router objects from each of your microservice files within the 'endpoints' directory
from endpoints.pypi import router as pypi_router
from endpoints.npm import router as npm_router
from endpoints.github_ep import router as github_router
from endpoints.hn import router as hn_router
from endpoints.reddit import router as reddit_router
from endpoints.so import router as stackoverflow_router

# Create the main FastAPI application
app = FastAPI(
    title="Developer AI Agent Aggregator",
    description="A single API to fetch data from multiple developer platforms.",
    version="1.0.0"
)

# Include each router with a specific prefix
# This is what organizes your API docs into sections

app.include_router(pypi_router, prefix="/pypi", tags=["PyPI"])
app.include_router(npm_router, prefix="/npm", tags=["npm"])
app.include_router(github_router, prefix="/github", tags=["GitHub"])
app.include_router(hn_router, prefix="/hackernews", tags=["Hacker News"])
app.include_router(reddit_router, prefix="/reddit", tags=["Reddit"])
app.include_router(stackoverflow_router, prefix="/stackoverflow", tags=["Stack Overflow"])


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the Aggregator API!"}

# This block allows you to run the main aggregator directly
if __name__ == "__main__":
    # The app location is now 'aggregator.main:app' as it's run from the parent directory
    uvicorn.run("aggregator.main:app", host="127.0.0.1", port=8000, reload=True)

