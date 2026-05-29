import hashlib

import httpx

from models.job import JobListing
from utils.text import strip_html, truncate

_BASE = "https://remotive.com/api/remote-jobs"


async def search(title: str, max_results: int = 25) -> list[JobListing]:
    params = {"search": title, "limit": max_results}

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(_BASE, params=params)
        resp.raise_for_status()
        data = resp.json()

    listings: list[JobListing] = []
    for job in data.get("jobs", [])[:max_results]:
        job_url = job.get("url", "")
        if not job_url:
            continue
        listings.append(
            JobListing(
                id=hashlib.md5(job_url.encode()).hexdigest(),
                title=job.get("title", ""),
                company=job.get("company_name", ""),
                location=job.get("candidate_required_location", "Remote"),
                url=job_url,
                description=truncate(strip_html(job.get("description", ""))),
                source="remotive",
            )
        )
    return listings
