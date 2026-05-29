from pydantic import BaseModel, Field


class ParsedResume(BaseModel):
    name: str = ""
    email: str = ""
    skills: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    years_of_experience: float = 0.0
    past_titles: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    summary: str = ""
    raw_text: str = ""
