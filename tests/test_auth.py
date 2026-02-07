from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


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
