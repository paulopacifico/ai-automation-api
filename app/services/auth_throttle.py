from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings

KEY_PREFIX = "auth:login-throttle"
STATE_TTL_SECONDS = 3600
SOFT_THRESHOLD = 5
HARD_THRESHOLD = 10
BASE_DELAY_SECONDS = 30
MAX_DELAY_SECONDS = 300
BLOCK_SECONDS = 300

_memory_store: dict[str, tuple[dict[str, int], int]] = {}
_memory_lock = threading.Lock()
_redis_client: Redis | None = None
_redis_client_lock = threading.Lock()


@dataclass(frozen=True)
class ThrottleDecision:
    allowed: bool
    retry_after: int = 0
    detail: str = ""


def _now() -> int:
    return int(time.time())


def _normalized_email(email: str) -> str:
    return email.strip().lower()


def _key(ip_address: str, email: str) -> str:
    return f"{KEY_PREFIX}:{ip_address}:{_normalized_email(email)}"


def _get_redis_client() -> Redis | None:
    global _redis_client
    if not settings.redis_url:
        return None

    if _redis_client is None:
        with _redis_client_lock:
            if _redis_client is None:
                _redis_client = Redis.from_url(settings.redis_url)
    return _redis_client


def _load_state(key: str) -> dict[str, int] | None:
    client = _get_redis_client()
    if client is not None:
        try:
            raw = client.get(key)
            if raw:
                payload = json.loads(raw)
                if isinstance(payload, dict):
                    return {k: int(v) for k, v in payload.items() if isinstance(v, int | float)}
        except (RedisError, ValueError, TypeError):
            pass

    now = _now()
    with _memory_lock:
        entry = _memory_store.get(key)
        if entry is None:
            return None
        state, expires_at = entry
        if expires_at <= now:
            _memory_store.pop(key, None)
            return None
        return state


def _save_state(key: str, state: dict[str, int], ttl: int) -> None:
    ttl = max(1, ttl)
    client = _get_redis_client()
    if client is not None:
        try:
            client.setex(key, ttl, json.dumps(state))
            return
        except (RedisError, TypeError, ValueError):
            pass

    with _memory_lock:
        _memory_store[key] = (state, _now() + ttl)


def _delete_state(key: str) -> None:
    client = _get_redis_client()
    if client is not None:
        try:
            client.delete(key)
        except RedisError:
            pass

    with _memory_lock:
        _memory_store.pop(key, None)


def check_login_allowed(ip_address: str, email: str) -> ThrottleDecision:
    key = _key(ip_address, email)
    state = _load_state(key)
    if state is None:
        return ThrottleDecision(allowed=True)

    now = _now()
    blocked_until = int(state.get("blocked_until", 0))
    if blocked_until > now:
        retry_after = blocked_until - now
        return ThrottleDecision(
            allowed=False,
            retry_after=retry_after,
            detail="Too many failed login attempts. Try again later.",
        )

    next_allowed_at = int(state.get("next_allowed_at", 0))
    if next_allowed_at > now:
        retry_after = next_allowed_at - now
        return ThrottleDecision(
            allowed=False,
            retry_after=retry_after,
            detail="Too many failed login attempts. Slow down and try again shortly.",
        )

    return ThrottleDecision(allowed=True)


def register_failed_login(ip_address: str, email: str) -> None:
    key = _key(ip_address, email)
    now = _now()
    previous = _load_state(key) or {}

    first_failure_at = int(previous.get("first_failure_at", now))
    if now - first_failure_at > STATE_TTL_SECONDS:
        first_failure_at = now
        failures = 0
    else:
        failures = int(previous.get("failures", 0))

    failures += 1
    next_allowed_at = now
    blocked_until = 0

    if failures >= HARD_THRESHOLD:
        blocked_until = now + BLOCK_SECONDS
        next_allowed_at = blocked_until
    elif failures >= SOFT_THRESHOLD:
        exponent = failures - SOFT_THRESHOLD
        delay = min(BASE_DELAY_SECONDS * (2**exponent), MAX_DELAY_SECONDS)
        next_allowed_at = now + delay

    state = {
        "failures": failures,
        "first_failure_at": first_failure_at,
        "next_allowed_at": next_allowed_at,
        "blocked_until": blocked_until,
    }

    ttl = max(
        STATE_TTL_SECONDS,
        next_allowed_at - now,
        blocked_until - now,
    )
    _save_state(key, state, ttl)


def clear_failed_logins(ip_address: str, email: str) -> None:
    _delete_state(_key(ip_address, email))


def reset_failed_logins_for_tests() -> None:
    with _memory_lock:
        _memory_store.clear()

    client = _get_redis_client()
    if client is not None:
        try:
            keys = list(client.scan_iter(f"{KEY_PREFIX}:*"))
            if keys:
                client.delete(*keys)
        except RedisError:
            pass
