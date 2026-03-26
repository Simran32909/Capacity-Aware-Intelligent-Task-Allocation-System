"""User CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task, TaskStatus, User
from app.schemas import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    user = User(
        name=payload.name.strip(),
        skills=payload.skills,
        weekly_capacity_hours=payload.weekly_capacity_hours,
        current_assigned_hours=payload.current_assigned_hours,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)).all())


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)) -> None:
    """Remove a team member. Their assigned tasks become Unassigned."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    assigned = db.scalars(
        select(Task).where(Task.assigned_user_id == user_id),
    ).all()
    for t in assigned:
        t.assigned_user_id = None
        t.status = TaskStatus.UNASSIGNED

    db.delete(user)
    db.commit()
