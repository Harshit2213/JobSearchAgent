from datetime import datetime, timezone

from sqlalchemy import String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from models.application import ApplicationStatus

DATABASE_URL = "sqlite:///./data/jobs.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class ApplicationRow(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_title: Mapped[str] = mapped_column(String(256))
    company: Mapped[str] = mapped_column(String(256))
    job_url: Mapped[str] = mapped_column(String(2048))
    source: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(32), default=ApplicationStatus.SAVED)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(String(32), default="")
    updated_at: Mapped[str] = mapped_column(String(32), default="")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_application(db: Session, job_title: str, company: str, job_url: str, source: str = "") -> ApplicationRow:
    now = _now()
    row = ApplicationRow(
        job_title=job_title,
        company=company,
        job_url=job_url,
        source=source,
        status=ApplicationStatus.SAVED,
        notes="",
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_application(db: Session, app_id: int) -> ApplicationRow | None:
    return db.get(ApplicationRow, app_id)


def list_applications(db: Session) -> list[ApplicationRow]:
    return db.query(ApplicationRow).order_by(ApplicationRow.updated_at.desc()).all()


def update_application(db: Session, app_id: int, status: str, notes: str) -> ApplicationRow | None:
    row = db.get(ApplicationRow, app_id)
    if row is None:
        return None
    row.status = status
    row.notes = notes
    row.updated_at = _now()
    db.commit()
    db.refresh(row)
    return row
