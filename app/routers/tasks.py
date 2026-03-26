"""Task creation and listing with auto-assignment."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task, TaskPriority, TaskStatus
from app.schemas import TaskCreate, TaskPrioritySchema, TaskRead, TaskStatusSchema
from app.services.allocation import find_best_user

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _task_to_read(task: Task, allocation_message: str | None = None) -> TaskRead:
    return TaskRead(
        id=task.id,
        title=task.title,
        required_skill=task.required_skill,
        estimated_hours=task.estimated_hours,
        priority=TaskPrioritySchema(task.priority.value),
        status=TaskStatusSchema(task.status.value),
        assigned_user_id=task.assigned_user_id,
        allocation_message=allocation_message,
    )


@router.post("", response_model=TaskRead)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> TaskRead:
    task = Task(
        title=payload.title.strip(),
        required_skill=payload.required_skill.strip(),
        estimated_hours=payload.estimated_hours,
        priority=TaskPriority(payload.priority.value),
        status=TaskStatus.UNASSIGNED,
    )
    db.add(task)
    db.flush()

    assignee, failure_reason = find_best_user(
        db,
        required_skill=task.required_skill,
        estimated_hours=task.estimated_hours,
    )
    msg: str | None = None
    if assignee is not None:
        task.assigned_user_id = assignee.id
        task.status = TaskStatus.ASSIGNED
        assignee.current_assigned_hours += task.estimated_hours
    else:
        msg = failure_reason

    db.commit()
    db.refresh(task)
    return _task_to_read(task, allocation_message=msg)


@router.get("", response_model=list[TaskRead])
def list_tasks(db: Session = Depends(get_db)) -> list[TaskRead]:
    tasks = list(db.scalars(select(Task).order_by(Task.id)).all())
    return [_task_to_read(t) for t in tasks]
