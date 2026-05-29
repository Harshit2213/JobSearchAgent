import hashlib

import httpx

from models.job import JobListing
from utils.text import strip_html, truncate

_BASE = "https://www.themuse.com/api/public/jobs"


async def search(title: str, max_results: int = 25) -> list[JobListing]:
    params = {"page": 1, "descending": "true", "category": title}

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(_BASE, params=params)
        resp.raise_for_status()
        data = resp.json()

    listings: list[JobListing] = []
    for job in data.get("results", [])[:max_results]:
        job_url = job.get("refs", {}).get("landing_page", "")
        if not job_url:
            continue
        locations = job.get("locations", [])
        location = locations[0].get("name", "") if locations else ""
        listings.append(
            JobListing(
                id=hashlib.md5(job_url.encode()).hexdigest(),
                title=job.get("name", ""),
                company=job.get("company", {}).get("name", ""),
                location=location,
                url=job_url,
                description=truncate(strip_html(job.get("contents", ""))),
                source="the_muse",
            )
        )
    return listings
