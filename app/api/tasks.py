from uuid import UUID

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.ai_classifier import AIClassifier, DEFAULT_CLASSIFICATION

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> Task:
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
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/tasks/{id}", response_model=TaskResponse)
def get_task(id: UUID, db: Session = Depends(get_db)) -> Task:
    task = db.get(Task, id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.get("/tasks", response_model=list[TaskResponse])
def list_tasks(db: Session = Depends(get_db)) -> list[Task]:
    result = db.execute(select(Task).order_by(Task.created_at.desc()))
    return list(result.scalars().all())


@router.patch("/tasks/{id}", response_model=TaskResponse)
def update_task(id: UUID, payload: TaskUpdate, db: Session = Depends(get_db)) -> Task:
    task = db.get(Task, id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task
