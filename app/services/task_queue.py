from __future__ import annotations

from redis import Redis
from rq import Queue, Retry

from app.core.config import settings


def _queue() -> Queue:
    connection = Redis.from_url(settings.redis_url)
    return Queue(settings.task_queue_name, connection=connection)


def enqueue_task_classification(task_id: str) -> None:
    queue = _queue()
    retry = Retry(max=settings.task_queue_retry_max, interval=[10, 30, 60])
    queue.enqueue(
        "app.jobs.task_classification.classify_task_job",
        task_id,
        retry=retry,
        job_timeout=60,
    )
