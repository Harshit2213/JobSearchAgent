from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db, list_applications, update_application
from models.application import ApplicationOut, ApplicationUpdate

router = APIRouter(prefix="/api", tags=["applications"])


@router.get("/applications", response_model=list[ApplicationOut])
def get_applications(db: Session = Depends(get_db)):
    return list_applications(db)


@router.put("/applications/{app_id}/status", response_model=ApplicationOut)
def set_status(app_id: int, body: ApplicationUpdate, db: Session = Depends(get_db)):
    row = update_application(db, app_id, body.status, body.notes)
    if row is None:
        raise HTTPException(status_code=404, detail="Application not found.")
    return row
