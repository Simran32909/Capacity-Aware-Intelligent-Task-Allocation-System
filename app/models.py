"""SQLAlchemy ORM models: User and Task."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    pass


class TaskPriority(str, enum.Enum):
    HIGH = "High"
    MED = "Med"
    LOW = "Low"


class TaskStatus(str, enum.Enum):
    UNASSIGNED = "Unassigned"
    ASSIGNED = "Assigned"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # List of skill names stored as JSON array in SQLite.
    skills: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    weekly_capacity_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    current_assigned_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="assigned_user",
        foreign_keys="Task.assigned_user_id",
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    required_skill: Mapped[str] = mapped_column(String(255), nullable=False)
    estimated_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=TaskStatus.UNASSIGNED,
    )
    assigned_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    assigned_user: Mapped["User | None"] = relationship(
        "User",
        back_populates="tasks",
        foreign_keys=[assigned_user_id],
    )
