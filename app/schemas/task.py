from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.task import TaskStatus


class TaskCreate(BaseModel):
    title: str
    description: str | None = None


class TaskUpdate(BaseModel):
    status: TaskStatus | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    status: TaskStatus
    category: str | None = None
    priority: str | None = None
    estimated_duration: int | None = None
    created_at: datetime
    updated_at: datetime
