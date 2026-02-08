from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.database import get_db
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import (
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth_throttle import (
    check_login_allowed,
    clear_failed_logins,
    register_failed_login,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _token_response(user: User) -> tuple[TokenResponse, str, datetime]:
    role = user.role.value if hasattr(user.role, "value") else str(user.role)
    access_token = create_access_token(str(user.id), role)
    refresh_token, refresh_expiry = create_refresh_token(str(user.id), role)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    ), refresh_token, refresh_expiry


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.rate_limit_auth)
def register(request: Request, payload: UserCreate, db: Session = Depends(get_db)) -> User:
    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.rate_limit_auth)
def login(request: Request, payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    client_ip = get_remote_address(request)
    throttle = check_login_allowed(client_ip, payload.email)
    if not throttle.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=throttle.detail,
            headers={"Retry-After": str(throttle.retry_after)},
        )

    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        register_failed_login(client_ip, payload.email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

    clear_failed_logins(client_ip, payload.email)
    response, refresh_token, refresh_expiry = _token_response(user)
    token_entry = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=refresh_expiry,
    )
    db.add(token_entry)
    db.commit()
    return response


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("5/minute")
def refresh(request: Request, payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        decoded = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    token_hash = hash_token(payload.refresh_token)
    token_entry = db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    ).scalar_one_or_none()

    if token_entry is None or token_entry.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")

    if token_entry.expires_at < _utc_now():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    user = db.get(User, token_entry.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")

    # rotate refresh token
    token_entry.revoked = True
    response, new_refresh, new_expiry = _token_response(user)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(new_refresh),
            expires_at=new_expiry,
        )
    )
    db.commit()
    return response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
def logout(request: Request, payload: LogoutRequest, db: Session = Depends(get_db)) -> None:
    token_hash = hash_token(payload.refresh_token)
    token_entry = db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    ).scalar_one_or_none()
    if token_entry:
        token_entry.revoked = True
        db.commit()
    return None


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user
