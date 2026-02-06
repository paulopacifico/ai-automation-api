from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app import models  # noqa: F401
from app.models.task import Task, TaskStatus
from app.services.ai_classifier import AIClassifier, DEFAULT_CLASSIFICATION

logger = logging.getLogger(__name__)


def _apply_classification(task: Task, classification: dict) -> None:
    task.category = classification["category"]
    task.priority = classification["priority"]
    task.estimated_duration = classification["estimated_duration"]


def classify_task_record(db: Session, task: Task) -> None:
    if task.status == TaskStatus.COMPLETED:
        return

    try:
        classifier = AIClassifier()
        classification = classifier.classify_task(task.title, task.description)
        _apply_classification(task, classification)
        task.status = TaskStatus.PENDING
    except Exception:
        logger.exception("AI classification failed for task_id=%s", task.id)
        _apply_classification(task, DEFAULT_CLASSIFICATION)
        task.status = TaskStatus.FAILED


def classify_task_by_id(task_id: str) -> None:
    with SessionLocal() as db:
        task = db.get(Task, UUID(task_id))
        if task is None:
            logger.warning("Task not found for classification: %s", task_id)
            return
        if task.status != TaskStatus.PROCESSING:
            return

        classify_task_record(db, task)
        db.commit()
