from pydantic import BaseModel, Field


class JobListing(BaseModel):
    id: str = ""
    title: str
    company: str
    location: str = ""
    url: str
    description: str = ""
    salary_min: float | None = None
    salary_max: float | None = None
    source: str = ""


class JobScore(BaseModel):
    score: int = Field(ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    summary: str = ""


class MatchedJob(BaseModel):
    listing: JobListing
    score: JobScore


class TailoredApplication(BaseModel):
    original_bullets: list[str] = Field(default_factory=list)
    tailored_bullets: list[str] = Field(default_factory=list)
    cover_letter: str = ""


class CompanyResearch(BaseModel):
    snapshot: str = ""
    red_flags: list[str] = Field(default_factory=list)
    green_flags: list[str] = Field(default_factory=list)


class QAPair(BaseModel):
    question: str
    answer: str


class InterviewPrep(BaseModel):
    qa_pairs: list[QAPair] = Field(default_factory=list)
