"""Danger zone: wipe all users and tasks (for demos / fresh start)."""

from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task, User

router = APIRouter(prefix="/reset", tags=["admin"])


@router.post("")
def reset_all(db: Session = Depends(get_db)) -> dict[str, str]:
    """Delete every task and every user. SQLite DB is left empty of CAIT data."""
    db.execute(delete(Task))
    db.execute(delete(User))
    db.commit()
    return {"status": "ok", "message": "All tasks and users removed."}
