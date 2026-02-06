import os
from typing import Iterator

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/automation_test",
)
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ["TASK_CLASSIFICATION_MODE"] = "sync"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.main import app


@pytest.fixture()
def db_session() -> Iterator[Session]:
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def _clean_tasks(db_session: Session) -> None:
    db_session.execute(text("TRUNCATE TABLE refresh_tokens, tasks, users RESTART IDENTITY CASCADE"))
    db_session.commit()


@pytest.fixture()
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    email = "user@example.com"
    password = "ChangeMe123"
    response = client.post("/auth/register", json={"email": email, "password": password})
    if response.status_code not in (201, 409):
        raise AssertionError(f"register failed: {response.status_code} {response.text}")
    response = client.post("/auth/login", json={"email": email, "password": password})
    if response.status_code != 200:
        raise AssertionError(f"login failed: {response.status_code} {response.text}")
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
