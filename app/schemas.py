"""Pydantic request/response models for the API."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class TaskPrioritySchema(str, Enum):
    HIGH = "High"
    MED = "Med"
    LOW = "Low"


class TaskStatusSchema(str, Enum):
    UNASSIGNED = "Unassigned"
    ASSIGNED = "Assigned"


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    skills: list[str] = Field(default_factory=list)
    weekly_capacity_hours: int = Field(..., ge=0)
    current_assigned_hours: int = Field(default=0, ge=0)

    @field_validator("skills", mode="before")
    @classmethod
    def strip_skills(cls, v: list[str]) -> list[str]:
        if not isinstance(v, list):
            return v
        return [s.strip() for s in v if isinstance(s, str) and s.strip()]


class UserRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    skills: list[str]
    weekly_capacity_hours: int
    current_assigned_hours: int


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    required_skill: str = Field(..., min_length=1, max_length=255)
    estimated_hours: int = Field(..., gt=0)
    priority: TaskPrioritySchema


class TaskRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    required_skill: str
    estimated_hours: int
    priority: TaskPrioritySchema
    status: TaskStatusSchema
    assigned_user_id: int | None
    allocation_message: str | None = None


class DashboardUserUtilization(BaseModel):
    user_id: int
    name: str
    weekly_capacity_hours: int
    current_assigned_hours: int
    utilization_rate: float


class DashboardResponse(BaseModel):
    total_tasks: int
    team_utilization: list[DashboardUserUtilization]
    overloaded_users: list[DashboardUserUtilization]
