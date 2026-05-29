import hashlib

import httpx

from models.job import JobListing
from utils.config import settings
from utils.text import strip_html, truncate

_BASE = "https://api.adzuna.com/v1/api/jobs"


async def search(title: str, location: str = "", max_results: int = 25) -> list[JobListing]:
    params: dict = {
        "app_id": settings.adzuna_app_id,
        "app_key": settings.adzuna_app_key,
        "results_per_page": min(max_results, 50),
        "what": title,
        "content-type": "application/json",
    }
    if location:
        params["where"] = location

    url = f"{_BASE}/{settings.adzuna_country}/search/1"

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    listings: list[JobListing] = []
    for job in data.get("results", []):
        job_url = job.get("redirect_url", "")
        if not job_url:
            continue
        listings.append(
            JobListing(
                id=hashlib.md5(job_url.encode()).hexdigest(),
                title=job.get("title", ""),
                company=job.get("company", {}).get("display_name", ""),
                location=job.get("location", {}).get("display_name", ""),
                url=job_url,
                description=truncate(strip_html(job.get("description", ""))),
                salary_min=job.get("salary_min"),
                salary_max=job.get("salary_max"),
                source="adzuna",
            )
        )
    return listings
