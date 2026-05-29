from enum import Enum

from pydantic import BaseModel


class ApplicationStatus(str, Enum):
    SAVED = "saved"
    APPLIED = "applied"
    PHONE_SCREEN = "phone_screen"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"


class ApplicationCreate(BaseModel):
    job_title: str
    company: str
    job_url: str
    source: str = ""
    notes: str = ""


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus
    notes: str = ""


class ApplicationOut(BaseModel):
    id: int
    job_title: str
    company: str
    job_url: str
    source: str
    status: ApplicationStatus
    notes: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
