from datetime import datetime
import time

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


def _create_task(client: TestClient, payload: dict | None = None) -> dict:
    if payload is None:
        payload = {"title": "Write tests", "description": "Add pytest coverage"}
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_and_get_task(monkeypatch) -> None:
    monkeypatch.setattr(tasks_module, "AIClassifier", lambda: DummyClassifier())

    client = TestClient(app)
    payload = {"title": "Write tests", "description": "Add pytest coverage"}
    created = _create_task(client, payload)
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


def test_create_task_ai_failure_uses_defaults(monkeypatch) -> None:
    class FailingClassifier:
        def classify_task(self, title: str, description: str | None) -> dict[str, object]:
            raise RuntimeError("AI failure")

    monkeypatch.setattr(tasks_module, "AIClassifier", lambda: FailingClassifier())

    client = TestClient(app)
    payload = {"title": "Fallback test", "description": "Should use defaults"}

    create_resp = client.post("/tasks", json=payload)
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["category"] == "general"
    assert created["priority"] == "medium"
    assert created["estimated_duration"] == 30


def test_get_task_not_found() -> None:
    client = TestClient(app)
    resp = client.get("/tasks/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_patch_task_status_success(monkeypatch) -> None:
    """Atualiza apenas o status de uma task existente."""
    monkeypatch.setattr(tasks_module, "AIClassifier", lambda: DummyClassifier())

    client = TestClient(app)
    created = _create_task(client)

    resp = client.patch(f"/tasks/{created['id']}", json={"status": "processing"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "processing"


def test_patch_task_multiple_fields(monkeypatch) -> None:
    """Atualiza status, priority e estimated_duration juntos."""
    monkeypatch.setattr(tasks_module, "AIClassifier", lambda: DummyClassifier())

    client = TestClient(app)
    created = _create_task(client)

    payload = {"status": "completed", "priority": "high", "estimated_duration": 120}
    resp = client.patch(f"/tasks/{created['id']}", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["priority"] == "high"
    assert data["estimated_duration"] == 120


def test_patch_task_not_found() -> None:
    """Retorna 404 para UUID inexistente."""
    client = TestClient(app)
    resp = client.patch("/tasks/00000000-0000-0000-0000-000000000000", json={"status": "processing"})
    assert resp.status_code == 404


def test_patch_task_invalid_status(monkeypatch) -> None:
    """Retorna 422 para status fora do enum."""
    monkeypatch.setattr(tasks_module, "AIClassifier", lambda: DummyClassifier())

    client = TestClient(app)
    created = _create_task(client)

    resp = client.patch(f"/tasks/{created['id']}", json={"status": "invalid"})
    assert resp.status_code == 422


def test_patch_task_invalid_estimated_duration(monkeypatch) -> None:
    """Retorna 422 para duração negativa ou > 10080."""
    monkeypatch.setattr(tasks_module, "AIClassifier", lambda: DummyClassifier())

    client = TestClient(app)
    created = _create_task(client)

    resp_low = client.patch(f"/tasks/{created['id']}", json={"estimated_duration": 0})
    assert resp_low.status_code == 422

    resp_high = client.patch(f"/tasks/{created['id']}", json={"estimated_duration": 10081})
    assert resp_high.status_code == 422


def test_patch_task_updates_timestamp(monkeypatch) -> None:
    """Verifica que updated_at foi atualizado."""
    monkeypatch.setattr(tasks_module, "AIClassifier", lambda: DummyClassifier())

    client = TestClient(app)
    created = _create_task(client)

    before = datetime.fromisoformat(created["updated_at"])
    time.sleep(1)

    resp = client.patch(f"/tasks/{created['id']}", json={"status": "processing"})
    assert resp.status_code == 200
    after = datetime.fromisoformat(resp.json()["updated_at"])
    assert after > before


def test_patch_task_partial_update(monkeypatch) -> None:
    """Campos não enviados permanecem inalterados."""
    monkeypatch.setattr(tasks_module, "AIClassifier", lambda: DummyClassifier())

    client = TestClient(app)
    created = _create_task(client)

    resp = client.patch(f"/tasks/{created['id']}", json={"priority": "urgent"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["priority"] == "urgent"
    assert data["status"] == created["status"]
