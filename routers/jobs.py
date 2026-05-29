import html

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from agents.job_discovery import JobDiscoveryAgent
from agents.job_matching import JobMatchingAgent
from agents.tailoring import TailoringAgent
from models.job import JobListing, MatchedJob, TailoredApplication
from models.resume import ParsedResume
from utils.limiter import limiter

router = APIRouter(prefix="/api", tags=["jobs"])


class SearchRequest(BaseModel):
    job_title: str = Field(min_length=1, max_length=100)
    location: str = Field(default="", max_length=100)
    profile: ParsedResume


class SearchResponse(BaseModel):
    jobs: list[MatchedJob]
    total: int


class TailorRequest(BaseModel):
    job: JobListing
    profile: ParsedResume


@router.post("/search-jobs", response_model=SearchResponse)
@limiter.limit("10/minute")
async def search_jobs(request: Request, body: SearchRequest):
    clean_title = html.escape(body.job_title.strip())
    clean_location = html.escape(body.location.strip())

    listings = await JobDiscoveryAgent().discover(clean_title, clean_location)
    matched = await JobMatchingAgent().score_all(body.profile, listings)

    return SearchResponse(jobs=matched, total=len(matched))


@router.post("/jobs/tailor", response_model=TailoredApplication)
@limiter.limit("10/minute")
async def tailor_job(request: Request, body: TailorRequest):
    return await TailoringAgent().tailor(body.profile, body.job)
