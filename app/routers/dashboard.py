"""Aggregates for the dashboard (totals, utilization, overloaded users)."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task, User
from app.schemas import DashboardResponse, DashboardUserUtilization
from app.services.allocation import utilization_rate

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardResponse:
    total_tasks = db.scalar(select(func.count()).select_from(Task)) or 0
    users = list(db.scalars(select(User).order_by(User.id)).all())

    team_utilization: list[DashboardUserUtilization] = []
    for u in users:
        rate = utilization_rate(u)
        team_utilization.append(
            DashboardUserUtilization(
                user_id=u.id,
                name=u.name,
                weekly_capacity_hours=u.weekly_capacity_hours,
                current_assigned_hours=u.current_assigned_hours,
                utilization_rate=rate,
            )
        )

    overloaded = [row for row in team_utilization if row.utilization_rate >= 1.0]

    return DashboardResponse(
        total_tasks=total_tasks,
        team_utilization=team_utilization,
        overloaded_users=overloaded,
    )
