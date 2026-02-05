import os
from typing import Iterator

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/automation_test",
)


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
    db_session.execute(text("TRUNCATE TABLE tasks RESTART IDENTITY CASCADE"))
    db_session.commit()
