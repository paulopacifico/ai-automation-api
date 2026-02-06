from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health/live")
def live() -> dict:
    return {"status": "ok"}


@router.get("/health/ready")
def ready(db: Session = Depends(get_db)) -> tuple[dict, int]:
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return {"status": "degraded", "checks": {"database": "fail"}}, status.HTTP_503_SERVICE_UNAVAILABLE

    checks: dict[str, str] = {"database": "ok"}

    if settings.redis_url:
        try:
            import redis

            client = redis.Redis.from_url(settings.redis_url)
            client.ping()
            checks["redis"] = "ok"
        except Exception:
            return {"status": "degraded", "checks": {**checks, "redis": "fail"}}, status.HTTP_503_SERVICE_UNAVAILABLE

    return {"status": "ok", "checks": checks}, status.HTTP_200_OK


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}
