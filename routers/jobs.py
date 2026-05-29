import html

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from agents.job_discovery import JobDiscoveryAgent
from models.job import JobListing
from utils.limiter import limiter

router = APIRouter(prefix="/api", tags=["jobs"])


class SearchRequest(BaseModel):
    job_title: str = Field(min_length=1, max_length=100)
    location: str = Field(default="", max_length=100)


class SearchResponse(BaseModel):
    jobs: list[JobListing]
    total: int
    sources_failed: list[str] = []


@router.post("/search-jobs", response_model=SearchResponse)
@limiter.limit("10/minute")
async def search_jobs(request: Request, body: SearchRequest):
    clean_title = html.escape(body.job_title.strip())
    clean_location = html.escape(body.location.strip())

    agent = JobDiscoveryAgent()
    listings = await agent.discover(clean_title, clean_location)

    return SearchResponse(jobs=listings, total=len(listings))
