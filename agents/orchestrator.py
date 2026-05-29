import asyncio
import logging

from agents.job_discovery import JobDiscoveryAgent
from agents.job_matching import JobMatchingAgent
from agents.resume_parser import ResumeParserAgent
from agents.role_inference import RoleInferenceAgent
from models.job import MatchedJob
from models.resume import ParsedResume

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """Coordinates the full pipeline: parse → infer → discover → score."""

    async def run(
        self,
        content: bytes,
        mime: str,
        job_title: str | None = None,
        location: str = "",
    ) -> dict:
        # Step 1: Parse resume (sync Claude call; run in thread to avoid blocking event loop)
        logger.info("Orchestrator: parsing resume")
        profile: ParsedResume = await asyncio.to_thread(
            ResumeParserAgent().parse, content, mime
        )

        # Step 2: Infer roles when no title provided
        inferred_roles: list[str] = []
        final_title = job_title
        if not final_title:
            logger.info("Orchestrator: inferring roles")
            inferred_roles = await asyncio.to_thread(
                RoleInferenceAgent().infer, profile
            )
            final_title = inferred_roles[0] if inferred_roles else ""

        if not final_title:
            logger.warning("Orchestrator: no job title available, skipping search")
            return {
                "profile": profile,
                "inferred_roles": inferred_roles,
                "job_title": None,
                "jobs": [],
            }

        # Step 3: Discover jobs from all sources concurrently
        logger.info("Orchestrator: discovering jobs for '%s'", final_title)
        listings = await JobDiscoveryAgent().discover(final_title, location)

        # Step 4: Score and rank all discovered jobs
        logger.info("Orchestrator: scoring %d jobs", len(listings))
        matched: list[MatchedJob] = await JobMatchingAgent().score_all(profile, listings)

        logger.info("Orchestrator: done — %d matched jobs returned", len(matched))
        return {
            "profile": profile,
            "inferred_roles": inferred_roles,
            "job_title": final_title,
            "jobs": matched,
        }
