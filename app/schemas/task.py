from __future__ import annotations

from datetime import datetime
from uuid import UUID

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.task import TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = None
    priority: Optional[str] = None
    estimated_duration: Optional[int] = Field(None, ge=1, le=10080)

    @field_validator("estimated_duration")
    @classmethod
    def _validate_estimated_duration(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value < 1 or value > 10080:
            raise ValueError("estimated_duration must be between 1 and 10080 minutes")
        return value


class TaskUpdate(BaseModel):
    status: TaskStatus | None = None
    category: Literal["development", "testing", "deployment", "maintenance", "documentation"] | None = None
    priority: Literal["low", "medium", "high", "urgent"] | None = None
    estimated_duration: int | None = None

    @field_validator("category", "priority")
    @classmethod
    def _not_empty(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.strip():
            raise ValueError("must not be empty")
        return value

    @field_validator("estimated_duration")
    @classmethod
    def _validate_estimated_duration(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if not 1 <= value <= 10080:
            raise ValueError("must be between 1 and 10080 minutes")
        return value


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    status: TaskStatus
    category: str | None = None
    priority: str | None = None
    estimated_duration: int | None = None
    owner_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
