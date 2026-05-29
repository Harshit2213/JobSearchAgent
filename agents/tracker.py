from sqlalchemy.orm import Session

from db.database import (
    ApplicationRow,
    create_application,
    list_applications,
    update_application,
)
from models.job import JobListing


class TrackerAgent:
    def save(self, db: Session, job: JobListing) -> ApplicationRow:
        return create_application(
            db,
            job_title=job.title,
            company=job.company,
            job_url=job.url,
            source=job.source,
        )

    def update(
        self, db: Session, app_id: int, status: str, notes: str = ""
    ) -> ApplicationRow | None:
        return update_application(db, app_id, status, notes)

    def list_all(self, db: Session) -> list[ApplicationRow]:
        return list_applications(db)
