import asyncio
import logging

from integrations import adzuna, arbeitnow, remotive, the_muse
from models.job import JobListing
from utils.config import settings

logger = logging.getLogger(__name__)


class JobDiscoveryAgent:
    async def discover(self, title: str, location: str = "") -> list[JobListing]:
        tasks = [
            adzuna.search(title, location, settings.max_jobs_per_source),
            remotive.search(title, settings.max_jobs_per_source),
            the_muse.search(title, settings.max_jobs_per_source),
            arbeitnow.search(title, settings.max_jobs_per_source),
        ]

        batches = await asyncio.gather(*tasks, return_exceptions=True)

        seen_urls: set[str] = set()
        listings: list[JobListing] = []

        for source, batch in zip(["adzuna", "remotive", "the_muse", "arbeitnow"], batches):
            if isinstance(batch, Exception):
                logger.warning("Job source '%s' failed: %s", source, batch)
                continue
            for job in batch:
                if job.url and job.url not in seen_urls:
                    seen_urls.add(job.url)
                    listings.append(job)

        return listings
