from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import create_application, get_db, list_applications, update_application
from models.application import ApplicationCreate, ApplicationOut, ApplicationUpdate

router = APIRouter(prefix="/api", tags=["applications"])


@router.post("/applications", response_model=ApplicationOut, status_code=201)
def save_application(body: ApplicationCreate, db: Session = Depends(get_db)):
    row = create_application(
        db,
        job_title=body.job_title,
        company=body.company,
        job_url=body.job_url,
        source=body.source,
    )
    return row


@router.get("/applications", response_model=list[ApplicationOut])
def get_applications(db: Session = Depends(get_db)):
    return list_applications(db)


@router.put("/applications/{app_id}/status", response_model=ApplicationOut)
def set_status(app_id: int, body: ApplicationUpdate, db: Session = Depends(get_db)):
    row = update_application(db, app_id, body.status, body.notes)
    if row is None:
        raise HTTPException(status_code=404, detail="Application not found.")
    return row
