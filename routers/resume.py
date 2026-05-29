import html

from fastapi import APIRouter, File, Form, Request, UploadFile
from pydantic import BaseModel

from agents.resume_parser import ResumeParserAgent
from agents.role_inference import RoleInferenceAgent
from utils.config import settings
from utils.file_security import validate_upload
from utils.limiter import limiter


class UploadResponse(BaseModel):
    profile: dict
    inferred_roles: list[str]
    job_title: str | None


router = APIRouter(prefix="/api", tags=["resume"])


@router.post("/upload-resume", response_model=UploadResponse)
@limiter.limit("10/minute")
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    job_title: str | None = Form(default=None),
):
    content, mime = await validate_upload(file, settings.max_upload_bytes)

    # Sanitize optional job title: strip, cap length, escape HTML special chars
    clean_title: str | None = None
    if job_title:
        clean_title = html.escape(job_title.strip())[:100] or None

    profile = ResumeParserAgent().parse(content, mime)

    inferred: list[str] = []
    if not clean_title:
        inferred = RoleInferenceAgent().infer(profile)

    return UploadResponse(
        profile=profile.model_dump(exclude={"raw_text"}),
        inferred_roles=inferred,
        job_title=clean_title,
    )
