from datetime import datetime
import time

from fastapi.testclient import TestClient

import app.services.task_classification as classification_module


class DummyClassifier:
    def classify_task(self, title: str, description: str | None) -> dict[str, object]:
        return {
            "category": "testing",
            "priority": "low",
            "estimated_duration": 5,
        }


def _create_task(client: TestClient, headers: dict[str, str], payload: dict | None = None) -> dict:
    if payload is None:
        payload = {"title": "Write tests", "description": "Add pytest coverage"}
    response = client.post("/tasks", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


def test_create_and_get_task(monkeypatch, client: TestClient, auth_headers: dict[str, str]) -> None:
    monkeypatch.setattr(classification_module, "AIClassifier", lambda: DummyClassifier())

    payload = {"title": "Write tests", "description": "Add pytest coverage"}
    created = _create_task(client, auth_headers, payload)
    assert created["title"] == payload["title"]
    assert created["status"] == "pending"
    assert created["category"] == "testing"
    assert created["priority"] == "low"
    assert created["estimated_duration"] == 5

    task_id = created["id"]
    get_resp = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["id"] == task_id
    assert fetched["title"] == payload["title"]


def test_create_task_ai_failure_uses_defaults(monkeypatch, client: TestClient, auth_headers: dict[str, str]) -> None:
    class FailingClassifier:
        def classify_task(self, title: str, description: str | None) -> dict[str, object]:
            raise RuntimeError("AI failure")

    monkeypatch.setattr(classification_module, "AIClassifier", lambda: FailingClassifier())

    payload = {"title": "Fallback test", "description": "Should use defaults"}

    create_resp = client.post("/tasks", json=payload, headers=auth_headers)
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["category"] == "general"
    assert created["priority"] == "medium"
    assert created["estimated_duration"] == 30


def test_get_task_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.get("/tasks/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert resp.status_code == 404


def test_patch_task_status_success(monkeypatch, client: TestClient, auth_headers: dict[str, str]) -> None:
    """Atualiza apenas o status de uma task existente."""
    monkeypatch.setattr(classification_module, "AIClassifier", lambda: DummyClassifier())

    created = _create_task(client, auth_headers)

    resp = client.patch(f"/tasks/{created['id']}", json={"status": "processing"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "processing"


def test_patch_task_multiple_fields(monkeypatch, client: TestClient, auth_headers: dict[str, str]) -> None:
    """Atualiza status, priority e estimated_duration juntos."""
    monkeypatch.setattr(classification_module, "AIClassifier", lambda: DummyClassifier())

    created = _create_task(client, auth_headers)

    payload = {"status": "completed", "priority": "high", "estimated_duration": 120}
    resp = client.patch(f"/tasks/{created['id']}", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["priority"] == "high"
    assert data["estimated_duration"] == 120


def test_patch_task_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Retorna 404 para UUID inexistente."""
    resp = client.patch(
        "/tasks/00000000-0000-0000-0000-000000000000",
        json={"status": "processing"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_patch_task_invalid_status(monkeypatch, client: TestClient, auth_headers: dict[str, str]) -> None:
    """Retorna 422 para status fora do enum."""
    monkeypatch.setattr(classification_module, "AIClassifier", lambda: DummyClassifier())

    created = _create_task(client, auth_headers)

    resp = client.patch(f"/tasks/{created['id']}", json={"status": "invalid"}, headers=auth_headers)
    assert resp.status_code == 422


def test_patch_task_invalid_estimated_duration(monkeypatch, client: TestClient, auth_headers: dict[str, str]) -> None:
    """Retorna 422 para duração negativa ou > 10080."""
    monkeypatch.setattr(classification_module, "AIClassifier", lambda: DummyClassifier())

    created = _create_task(client, auth_headers)

    resp_low = client.patch(
        f"/tasks/{created['id']}",
        json={"estimated_duration": 0},
        headers=auth_headers,
    )
    assert resp_low.status_code == 422

    resp_high = client.patch(
        f"/tasks/{created['id']}",
        json={"estimated_duration": 10081},
        headers=auth_headers,
    )
    assert resp_high.status_code == 422


def test_patch_task_updates_timestamp(monkeypatch, client: TestClient, auth_headers: dict[str, str]) -> None:
    """Verifica que updated_at foi atualizado."""
    monkeypatch.setattr(classification_module, "AIClassifier", lambda: DummyClassifier())

    created = _create_task(client, auth_headers)

    before = datetime.fromisoformat(created["updated_at"])
    time.sleep(1)

    resp = client.patch(f"/tasks/{created['id']}", json={"status": "processing"}, headers=auth_headers)
    assert resp.status_code == 200
    after = datetime.fromisoformat(resp.json()["updated_at"])
    assert after > before


def test_patch_task_partial_update(monkeypatch, client: TestClient, auth_headers: dict[str, str]) -> None:
    """Campos não enviados permanecem inalterados."""
    monkeypatch.setattr(classification_module, "AIClassifier", lambda: DummyClassifier())

    created = _create_task(client, auth_headers)

    resp = client.patch(f"/tasks/{created['id']}", json={"priority": "urgent"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["priority"] == "urgent"
    assert data["status"] == created["status"]


def test_list_tasks_empty(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.get("/tasks", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_tasks_all(monkeypatch, client: TestClient, auth_headers: dict[str, str]) -> None:
    monkeypatch.setattr(classification_module, "AIClassifier", lambda: DummyClassifier())
    _create_task(client, auth_headers, {"title": "Task A", "description": "A"})
    _create_task(client, auth_headers, {"title": "Task B", "description": "B"})

    resp = client.get("/tasks", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


def test_list_tasks_filter_by_status(monkeypatch, client: TestClient, auth_headers: dict[str, str]) -> None:
    monkeypatch.setattr(classification_module, "AIClassifier", lambda: DummyClassifier())
    _create_task(client, auth_headers, {"title": "Task A", "description": "A"})
    task_b = _create_task(client, auth_headers, {"title": "Task B", "description": "B"})

    client.patch(f"/tasks/{task_b['id']}", json={"status": "completed"}, headers=auth_headers)
    resp = client.get("/tasks", params={"status": "completed"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == task_b["id"]


def test_list_tasks_filter_by_priority(monkeypatch, client: TestClient, auth_headers: dict[str, str]) -> None:
    monkeypatch.setattr(classification_module, "AIClassifier", lambda: DummyClassifier())
    _create_task(client, auth_headers, {"title": "Task A", "description": "A"})
    task_b = _create_task(client, auth_headers, {"title": "Task B", "description": "B"})

    client.patch(f"/tasks/{task_b['id']}", json={"priority": "urgent"}, headers=auth_headers)
    resp = client.get("/tasks", params={"priority": "urgent"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == task_b["id"]


def test_list_tasks_multiple_filters(monkeypatch, client: TestClient, auth_headers: dict[str, str]) -> None:
    monkeypatch.setattr(classification_module, "AIClassifier", lambda: DummyClassifier())
    _create_task(client, auth_headers, {"title": "Task A", "description": "A"})
    task_b = _create_task(client, auth_headers, {"title": "Task B", "description": "B"})

    client.patch(
        f"/tasks/{task_b['id']}",
        json={"status": "completed", "priority": "high", "category": "development"},
        headers=auth_headers,
    )
    resp = client.get(
        "/tasks",
        params={"status": "completed", "priority": "high", "category": "development"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == task_b["id"]


def test_list_tasks_pagination(monkeypatch, client: TestClient, auth_headers: dict[str, str]) -> None:
    monkeypatch.setattr(classification_module, "AIClassifier", lambda: DummyClassifier())
    _create_task(client, auth_headers, {"title": "Task A", "description": "A"})
    _create_task(client, auth_headers, {"title": "Task B", "description": "B"})
    _create_task(client, auth_headers, {"title": "Task C", "description": "C"})

    resp = client.get("/tasks", params={"limit": 2, "offset": 1}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


def test_list_tasks_sort_asc(monkeypatch, client: TestClient, auth_headers: dict[str, str]) -> None:
    monkeypatch.setattr(classification_module, "AIClassifier", lambda: DummyClassifier())
    _create_task(client, auth_headers, {"title": "Task A", "description": "A"})
    time.sleep(0.5)
    _create_task(client, auth_headers, {"title": "Task B", "description": "B"})

    resp = client.get("/tasks", params={"sort_by": "created_at", "sort_order": "asc"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["title"] == "Task A"


def test_list_tasks_sort_desc(monkeypatch, client: TestClient, auth_headers: dict[str, str]) -> None:
    monkeypatch.setattr(classification_module, "AIClassifier", lambda: DummyClassifier())
    _create_task(client, auth_headers, {"title": "Task A", "description": "A"})
    time.sleep(0.5)
    _create_task(client, auth_headers, {"title": "Task B", "description": "B"})

    resp = client.get("/tasks", params={"sort_by": "created_at", "sort_order": "desc"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["title"] == "Task B"


def test_list_tasks_invalid_limit(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.get("/tasks", params={"limit": 1000}, headers=auth_headers)
    assert resp.status_code == 422


def test_delete_task_success(monkeypatch, client: TestClient, auth_headers: dict[str, str]) -> None:
    monkeypatch.setattr(classification_module, "AIClassifier", lambda: DummyClassifier())
    created = _create_task(client, auth_headers)

    resp = client.delete(f"/tasks/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204


def test_delete_task_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.delete("/tasks/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert resp.status_code == 404


def test_delete_task_verify_deleted(monkeypatch, client: TestClient, auth_headers: dict[str, str]) -> None:
    monkeypatch.setattr(classification_module, "AIClassifier", lambda: DummyClassifier())
    created = _create_task(client, auth_headers)

    resp = client.delete(f"/tasks/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204

    get_resp = client.get(f"/tasks/{created['id']}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_delete_task_invalid_uuid(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.delete("/tasks/not-a-uuid", headers=auth_headers)
    assert resp.status_code == 422
