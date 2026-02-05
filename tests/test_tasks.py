from fastapi.testclient import TestClient

import app.api.tasks as tasks_module
from app.main import app


class DummyClassifier:
    def classify_task(self, title: str, description: str | None) -> dict[str, object]:
        return {
            "category": "testing",
            "priority": "low",
            "estimated_duration": 5,
        }


def test_create_and_get_task(monkeypatch) -> None:
    monkeypatch.setattr(tasks_module, "AIClassifier", lambda: DummyClassifier())

    client = TestClient(app)
    payload = {"title": "Write tests", "description": "Add pytest coverage"}

    create_resp = client.post("/tasks", json=payload)
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["title"] == payload["title"]
    assert created["status"] == "pending"
    assert created["category"] == "testing"
    assert created["priority"] == "low"
    assert created["estimated_duration"] == 5

    task_id = created["id"]
    get_resp = client.get(f"/tasks/{task_id}")
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["id"] == task_id
    assert fetched["title"] == payload["title"]


def test_get_task_not_found() -> None:
    client = TestClient(app)
    resp = client.get("/tasks/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
