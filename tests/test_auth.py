from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
import app.services.auth_throttle as auth_throttle


def _register_and_login(client: TestClient, email: str, password: str = "ChangeMe123") -> dict[str, str]:
    register = client.post("/auth/register", json={"email": email, "password": password})
    assert register.status_code == 201
    login = client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return login.json()


def test_inactive_user_me_returns_403(client: TestClient, db_session: Session) -> None:
    auth = _register_and_login(client, "inactive-user@example.com")
    token = auth["access_token"]

    user = db_session.execute(select(User).where(User.email == "inactive-user@example.com")).scalar_one()
    user.is_active = False
    db_session.commit()

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "User is inactive"


def test_revoked_refresh_token_returns_401(client: TestClient) -> None:
    auth = _register_and_login(client, "refresh-user@example.com")
    refresh_token = auth["refresh_token"]

    logout = client.post("/auth/logout", json={"refresh_token": refresh_token})
    assert logout.status_code == 204

    refresh = client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert refresh.status_code == 401
    assert refresh.json()["detail"] == "Refresh token revoked"


def test_login_progressive_backoff_and_reset(monkeypatch, client: TestClient) -> None:
    auth_throttle.reset_failed_logins_for_tests()
    current_time = {"value": 1_000_000}

    monkeypatch.setattr(auth_throttle, "_now", lambda: current_time["value"])
    monkeypatch.setattr(auth_throttle, "SOFT_THRESHOLD", 2)
    monkeypatch.setattr(auth_throttle, "HARD_THRESHOLD", 4)
    monkeypatch.setattr(auth_throttle, "BASE_DELAY_SECONDS", 10)
    monkeypatch.setattr(auth_throttle, "MAX_DELAY_SECONDS", 30)
    monkeypatch.setattr(auth_throttle, "BLOCK_SECONDS", 120)

    register = client.post(
        "/auth/register",
        json={"email": "backoff-user@example.com", "password": "ChangeMe123"},
    )
    assert register.status_code == 201

    for _ in range(2):
        failed = client.post(
            "/auth/login",
            json={"email": "backoff-user@example.com", "password": "WrongPass123"},
        )
        assert failed.status_code == 401

    throttled = client.post(
        "/auth/login",
        json={"email": "backoff-user@example.com", "password": "WrongPass123"},
    )
    assert throttled.status_code == 429
    assert throttled.headers.get("Retry-After") == "10"

    current_time["value"] += 11
    successful = client.post(
        "/auth/login",
        json={"email": "backoff-user@example.com", "password": "ChangeMe123"},
    )
    assert successful.status_code == 200

    post_reset = client.post(
        "/auth/login",
        json={"email": "backoff-user@example.com", "password": "WrongPass123"},
    )
    assert post_reset.status_code == 401


def test_login_hard_block_after_repeated_failures(monkeypatch, client: TestClient) -> None:
    auth_throttle.reset_failed_logins_for_tests()
    current_time = {"value": 2_000_000}

    monkeypatch.setattr(auth_throttle, "_now", lambda: current_time["value"])
    monkeypatch.setattr(auth_throttle, "SOFT_THRESHOLD", 2)
    monkeypatch.setattr(auth_throttle, "HARD_THRESHOLD", 3)
    monkeypatch.setattr(auth_throttle, "BASE_DELAY_SECONDS", 10)
    monkeypatch.setattr(auth_throttle, "MAX_DELAY_SECONDS", 30)
    monkeypatch.setattr(auth_throttle, "BLOCK_SECONDS", 120)

    register = client.post(
        "/auth/register",
        json={"email": "lock-user@example.com", "password": "ChangeMe123"},
    )
    assert register.status_code == 201

    for _ in range(2):
        failed = client.post(
            "/auth/login",
            json={"email": "lock-user@example.com", "password": "WrongPass123"},
        )
        assert failed.status_code == 401

    current_time["value"] += 11
    third_failure = client.post(
        "/auth/login",
        json={"email": "lock-user@example.com", "password": "WrongPass123"},
    )
    assert third_failure.status_code == 401

    blocked = client.post(
        "/auth/login",
        json={"email": "lock-user@example.com", "password": "WrongPass123"},
    )
    assert blocked.status_code == 429
    assert blocked.headers.get("Retry-After") == "120"
