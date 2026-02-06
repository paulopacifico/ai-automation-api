from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.tasks import router as tasks_router
from app.core.config import settings
from app.core.limiter import limiter

settings.validate_security()

app = FastAPI()

if settings.rate_limit_enabled:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(health_router)
