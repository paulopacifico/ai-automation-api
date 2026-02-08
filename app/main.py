from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.tasks import router as tasks_router
from app.core.config import Settings, settings
from app.core.limiter import limiter


def _request_is_secure(request: Request) -> bool:
    if request.url.scheme == "https":
        return True
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    return forwarded_proto.split(",")[0].strip().lower() == "https"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, *, app_settings: Settings) -> None:
        super().__init__(app)
        self._settings = app_settings

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", self._settings.referrer_policy)

        if self._settings.is_production() and _request_is_secure(request):
            response.headers.setdefault(
                "Strict-Transport-Security",
                f"max-age={self._settings.hsts_max_age_seconds}; includeSubDomains",
            )
        return response


def create_app(app_settings: Settings | None = None) -> FastAPI:
    config = app_settings or settings
    config.validate_security()

    app = FastAPI()

    if config.rate_limit_enabled:
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        app.add_middleware(SlowAPIMiddleware)

    if config.trusted_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.trusted_hosts)

    if config.cors_allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.cors_allowed_origins,
            allow_credentials=config.cors_allow_credentials,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
        )

    if config.is_production() and config.https_redirect_enabled:
        app.add_middleware(HTTPSRedirectMiddleware)

    if config.security_headers_enabled:
        app.add_middleware(SecurityHeadersMiddleware, app_settings=config)

    app.include_router(auth_router)
    app.include_router(tasks_router)
    app.include_router(health_router)
    return app


app = create_app()
