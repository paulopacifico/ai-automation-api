from uuid import UUID

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.task import Task, TaskStatus
from app.models.user import User, UserRole
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.ai_classifier import AIClassifier, DEFAULT_CLASSIFICATION

router = APIRouter()
logger = logging.getLogger(__name__)


def _authorize_task(task: Task, user: User) -> None:
    if user.role == UserRole.ADMIN:
        return
    if task.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    classification = DEFAULT_CLASSIFICATION
    try:
        classifier = AIClassifier()
        classification = classifier.classify_task(payload.title, payload.description)
    except Exception:
        logger.exception("AI classification failed; using defaults")

    task = Task(
        title=payload.title,
        description=payload.description,
        category=classification["category"],
        priority=classification["priority"],
        estimated_duration=classification["estimated_duration"],
        owner_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/tasks/{id}", response_model=TaskResponse)
def get_task(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    task = db.get(Task, id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    _authorize_task(task, current_user)
    return task


@router.get("/tasks", response_model=list[TaskResponse])
def list_tasks(
    status: TaskStatus | None = None,
    category: str | None = None,
    priority: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at", pattern="^(created_at|priority|status)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Task]:
    query = select(Task)

    if current_user.role != UserRole.ADMIN:
        query = query.where(Task.owner_id == current_user.id)

    if status is not None:
        query = query.where(Task.status == status)
    if category:
        query = query.where(Task.category == category)
    if priority:
        query = query.where(Task.priority == priority)

    if sort_by == "priority":
        order_col = Task.priority
    elif sort_by == "status":
        order_col = Task.status
    else:
        order_col = Task.created_at

    if sort_order == "desc":
        query = query.order_by(order_col.desc())
    else:
        query = query.order_by(order_col.asc())

    query = query.limit(limit).offset(offset)

    result = db.execute(query)
    return list(result.scalars().all())


@router.patch("/tasks/{id}", response_model=TaskResponse)
def update_task(
    id: UUID,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    task = db.get(Task, id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    _authorize_task(task, current_user)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete("/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    task = db.get(Task, id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    _authorize_task(task, current_user)

    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
