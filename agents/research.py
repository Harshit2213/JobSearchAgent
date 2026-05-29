from agents.base import BaseAgent
from models.job import CompanyResearch, JobListing

_RESEARCH_TOOL = {
    "name": "research_company",
    "description": "Extract company and role insights from a job description.",
    "input_schema": {
        "type": "object",
        "properties": {
            "snapshot": {
                "type": "string",
                "description": "2-3 sentence overview of the company inferred from the JD",
            },
            "green_flags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Positive signals: growth, culture, clear expectations, good benefits",
            },
            "red_flags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Concerning signals: vague scope, unrealistic requirements, warning language",
            },
        },
        "required": ["snapshot", "green_flags", "red_flags"],
    },
}

_SYSTEM = (
    "You are a career researcher. Analyse a job posting to surface company and role insights.\n\n"
    "Focus on:\n"
    "- Company stage and size signals (language, team structure, funding mentions)\n"
    "- Culture indicators (values language, work style, team dynamics)\n"
    "- Green flags: strong growth signals, clear role definition, realistic expectations\n"
    "- Red flags: vague responsibilities, 'wear many hats' overload, toxic language patterns\n\n"
    "Work only from the provided text — never invent facts not present in the posting."
)


class ResearchAgent(BaseAgent):
    _quality = "fast"
    async def research(self, job: JobListing) -> CompanyResearch:
        content = (
            f"Company: {job.company}\n"
            f"Title: {job.title}\n"
            f"Location: {job.location}\n\n"
            f"Job Description:\n{job.description}"
        )
        response = await self._acall(
            system=_SYSTEM,
            messages=[{"role": "user", "content": f"Analyse this posting:\n\n{content}"}],
            tools=[_RESEARCH_TOOL],
            tool_name="research_company",
            cache_system=True,
            max_tokens=1024,
        )
        data = self._extract_tool_input(response)
        return CompanyResearch(**data)
