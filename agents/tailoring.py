from agents.base import BaseAgent
from models.job import JobListing, TailoredApplication
from models.resume import ParsedResume

_TAILOR_TOOL = {
    "name": "tailor_application",
    "description": "Rewrite resume bullets and draft a cover letter for this specific job.",
    "input_schema": {
        "type": "object",
        "properties": {
            "original_bullets": {
                "type": "array",
                "items": {"type": "string"},
                "description": "The 5 most relevant existing achievements from the candidate's profile",
            },
            "tailored_bullets": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "The same 5 bullets rewritten to mirror the job description's language "
                    "and priorities. Keep factual accuracy — only change framing."
                ),
            },
            "cover_letter": {
                "type": "string",
                "description": (
                    "3-paragraph cover letter: "
                    "(1) compelling opening hook referencing the role, "
                    "(2) specific skills/experience match with examples, "
                    "(3) motivation + cultural fit close."
                ),
            },
        },
        "required": ["original_bullets", "tailored_bullets", "cover_letter"],
    },
}


class TailoringAgent(BaseAgent):
    def _build_system(self, profile: ParsedResume) -> str:
        return (
            "You are an expert career coach who tailors job applications.\n\n"
            "Rules:\n"
            "- Never fabricate experience or skills not present in the profile\n"
            "- Mirror the job description's vocabulary and priorities in rewrites\n"
            "- Keep bullet points concise and achievement-oriented (use metrics if present)\n"
            "- Cover letter must feel personal, not generic\n\n"
            "Candidate profile:\n"
            f"{profile.model_dump_json(indent=2, exclude={'raw_text'})}"
        )

    async def tailor(self, profile: ParsedResume, job: JobListing) -> TailoredApplication:
        system = self._build_system(profile)
        content = (
            f"Job Title: {job.title}\n"
            f"Company: {job.company}\n\n"
            f"Job Description:\n{job.description}"
        )
        response = await self._acall(
            system=system,
            messages=[{"role": "user", "content": f"Tailor this application:\n\n{content}"}],
            tools=[_TAILOR_TOOL],
            tool_name="tailor_application",
            cache_system=True,
            max_tokens=2048,
        )
        data = self._extract_tool_input(response)
        return TailoredApplication(**data)
