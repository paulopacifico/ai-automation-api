from __future__ import annotations

from app.services.task_classification import classify_task_by_id


def classify_task_job(task_id: str) -> None:
    classify_task_by_id(task_id)
