from fastapi import APIRouter, Request
from pydantic import BaseModel

from agents.interview_prep import InterviewPrepAgent
from models.job import InterviewPrep, JobListing
from models.resume import ParsedResume
from utils.limiter import limiter

router = APIRouter(prefix="/api", tags=["interview"])


class InterviewPrepRequest(BaseModel):
    job: JobListing
    profile: ParsedResume


@router.post("/jobs/interview-prep", response_model=InterviewPrep)
@limiter.limit("10/minute")
async def get_interview_prep(request: Request, body: InterviewPrepRequest):
    return await InterviewPrepAgent().prepare(body.profile, body.job)
