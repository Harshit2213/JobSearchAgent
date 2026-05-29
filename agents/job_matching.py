import asyncio
import logging

from agents.base import BaseAgent
from models.job import JobListing, JobScore, MatchedJob
from models.resume import ParsedResume

logger = logging.getLogger(__name__)

_SCORE_TOOL = {
    "name": "score_job",
    "description": "Score how well the candidate fits this job posting.",
    "input_schema": {
        "type": "object",
        "properties": {
            "score": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
                "description": "Overall fit score",
            },
            "strengths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Up to 4 reasons the candidate is a strong fit",
            },
            "missing_skills": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Skills or experience the JD requires that the candidate lacks",
            },
            "summary": {
                "type": "string",
                "description": "One sentence explaining the score",
            },
        },
        "required": ["score", "strengths", "missing_skills", "summary"],
    },
}

_SCORE_GUIDE = """
Score 0-100:
  90-100  Exceptional — candidate exceeds requirements
  70-89   Strong — meets most requirements, minor gaps
  50-69   Moderate — transferable skills but notable gaps
  0-49    Poor — significant mismatches
"""


class JobMatchingAgent(BaseAgent):
    _CONCURRENCY = 5  # max simultaneous Claude calls

    def _build_system(self, profile: ParsedResume) -> str:
        return (
            "You are a job matching expert. Score how well a candidate fits a job posting.\n\n"
            f"{_SCORE_GUIDE}\n\n"
            "Candidate profile:\n"
            f"{profile.model_dump_json(indent=2, exclude={'raw_text'})}"
        )

    async def _score_one(
        self, system: str, job: JobListing, sem: asyncio.Semaphore
    ) -> MatchedJob:
        async with sem:
            content = (
                f"Title: {job.title}\n"
                f"Company: {job.company}\n"
                f"Location: {job.location}\n\n"
                f"{job.description}"
            )
            response = await self._acall(
                system=system,
                messages=[{"role": "user", "content": f"Score this job:\n\n{content}"}],
                tools=[_SCORE_TOOL],
                tool_name="score_job",
                cache_system=True,
                max_tokens=512,
            )
            data = self._extract_tool_input(response)
            return MatchedJob(listing=job, score=JobScore(**data))

    async def score_all(
        self, profile: ParsedResume, jobs: list[JobListing]
    ) -> list[MatchedJob]:
        system = self._build_system(profile)
        sem = asyncio.Semaphore(self._CONCURRENCY)
        tasks = [self._score_one(system, job, sem) for job in jobs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        matched: list[MatchedJob] = []
        for job, result in zip(jobs, results):
            if isinstance(result, Exception):
                logger.warning("Scoring failed for '%s': %s", job.title, result)
                matched.append(
                    MatchedJob(
                        listing=job,
                        score=JobScore(score=0, summary="Scoring unavailable."),
                    )
                )
            else:
                matched.append(result)  # type: ignore[arg-type]

        return sorted(matched, key=lambda m: m.score.score, reverse=True)
