from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_app


def _settings_with(**overrides):
    app_settings = settings.model_copy(deep=True)
    app_settings.rate_limit_enabled = False
    app_settings.task_classification_mode = "sync"
    app_settings.redis_url = None
    app_settings.trusted_hosts = ["testserver", "localhost", "127.0.0.1"]
    app_settings.cors_allowed_origins = []
    app_settings.https_redirect_enabled = False
    app_settings.security_headers_enabled = True
    app_settings.environment = "development"

    for key, value in overrides.items():
        setattr(app_settings, key, value)
    return app_settings


def test_invalid_host_returns_400() -> None:
    app = create_app(_settings_with(trusted_hosts=["testserver", "api.example.com"]))
    client = TestClient(app)

    response = client.get("/health", headers={"Host": "evil.example.com"})

    assert response.status_code == 400


def test_cors_denies_disallowed_origin() -> None:
    app = create_app(
        _settings_with(
            cors_allowed_origins=["https://app.example.com"],
            cors_allow_credentials=True,
        )
    )
    client = TestClient(app)

    response = client.options(
        "/health",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_https_redirect_enabled_in_production() -> None:
    app = create_app(
        _settings_with(
            environment="production",
            https_redirect_enabled=True,
        )
    )
    client = TestClient(app, base_url="http://testserver")

    response = client.get("/health", follow_redirects=False)

    assert response.status_code in {307, 308}
    assert response.headers["location"].startswith("https://")


def test_security_headers_are_applied() -> None:
    app = create_app(_settings_with(environment="production", https_redirect_enabled=False))
    client = TestClient(app, base_url="https://testserver")

    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "strict-transport-security" in response.headers
