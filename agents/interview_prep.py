from agents.base import BaseAgent
from models.job import InterviewPrep, JobListing, QAPair
from models.resume import ParsedResume

_PREP_TOOL = {
    "name": "generate_interview_prep",
    "description": "Generate interview questions and model answers for a specific role.",
    "input_schema": {
        "type": "object",
        "properties": {
            "qa_pairs": {
                "type": "array",
                "description": (
                    "Exactly 8 pairs: 3 behavioral (STAR answers), "
                    "3 technical/role-specific, 2 company/culture fit"
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "answer": {
                            "type": "string",
                            "description": "Concise model answer (3-5 sentences) specific to this candidate",
                        },
                    },
                    "required": ["question", "answer"],
                },
            }
        },
        "required": ["qa_pairs"],
    },
}

_SYSTEM = (
    "You are an expert interview coach preparing a candidate for a specific role.\n\n"
    "Generate 8 likely interview questions with strong model answers:\n"
    "- 3 behavioral — use STAR format, draw from the candidate's actual experience\n"
    "- 3 technical/role-specific — based on the JD's required skills\n"
    "- 2 company/culture fit — based on the company's signals in the JD\n\n"
    "Rules:\n"
    "- Answers must reference THIS candidate's background, not generic advice\n"
    "- Never fabricate experience not present in the profile\n"
    "- Keep answers concise: 3-5 sentences each\n\n"
    "Candidate profile:\n{profile}"
)


class InterviewPrepAgent(BaseAgent):
    _quality = "fast"
    def _build_system(self, profile: ParsedResume) -> str:
        return _SYSTEM.format(
            profile=profile.model_dump_json(indent=2, exclude={"raw_text"})
        )

    async def prepare(self, profile: ParsedResume, job: JobListing) -> InterviewPrep:
        system = self._build_system(profile)
        content = (
            f"Role: {job.title}\n"
            f"Company: {job.company}\n\n"
            f"Job Description:\n{job.description}"
        )
        response = await self._acall(
            system=system,
            messages=[{"role": "user", "content": f"Generate interview prep for:\n\n{content}"}],
            tools=[_PREP_TOOL],
            tool_name="generate_interview_prep",
            cache_system=True,
            max_tokens=2048,
        )
        data = self._extract_tool_input(response)
        return InterviewPrep(qa_pairs=[QAPair(**p) for p in data.get("qa_pairs", [])])
