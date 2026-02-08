from __future__ import annotations

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(..., alias="DATABASE_URL")
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    rate_limit_enabled: bool = Field(True, alias="RATE_LIMIT_ENABLED")
    rate_limit_default: str = Field("100/minute", alias="RATE_LIMIT_DEFAULT")
    rate_limit_auth: str = Field("10/minute", alias="RATE_LIMIT_AUTH")
    redis_url: str | None = Field(None, alias="REDIS_URL")
    task_classification_mode: str = Field("async", alias="TASK_CLASSIFICATION_MODE")
    task_queue_name: str = Field("task-classification", alias="TASK_QUEUE_NAME")
    task_queue_retry_max: int = Field(3, alias="TASK_QUEUE_RETRY_MAX")
    environment: str = Field("development", validation_alias=AliasChoices("ENV", "APP_ENV"))
    trusted_hosts: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1", "testserver"],
        alias="TRUSTED_HOSTS",
    )
    cors_allowed_origins: list[str] = Field(default_factory=list, alias="CORS_ALLOWED_ORIGINS")
    cors_allow_credentials: bool = Field(False, alias="CORS_ALLOW_CREDENTIALS")
    https_redirect_enabled: bool = Field(False, alias="HTTPS_REDIRECT_ENABLED")
    security_headers_enabled: bool = Field(True, alias="SECURITY_HEADERS_ENABLED")
    hsts_max_age_seconds: int = Field(31536000, alias="HSTS_MAX_AGE_SECONDS")
    referrer_policy: str = Field("strict-origin-when-cross-origin", alias="REFERRER_POLICY")

    @field_validator("trusted_hosts", "cors_allowed_origins", mode="before")
    @classmethod
    def _parse_csv_list(cls, value: str | list[str] | tuple[str, ...] | None) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, tuple):
            return [str(item).strip() for item in value if str(item).strip()]
        return [str(item).strip() for item in value if str(item).strip()]

    def is_development(self) -> bool:
        return self.environment.lower() == "development"

    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    def validate_security(self) -> None:
        secret = self.jwt_secret_key.strip()
        if not secret:
            raise ValueError("JWT_SECRET_KEY must be set")
        if secret == "change-me" and not self.is_development():
            raise ValueError("JWT_SECRET_KEY must be set to a strong value outside development")
        if self.task_classification_mode not in {"sync", "async"}:
            raise ValueError("TASK_CLASSIFICATION_MODE must be 'sync' or 'async'")
        if self.task_classification_mode == "async" and not self.redis_url:
            raise ValueError("REDIS_URL must be set when TASK_CLASSIFICATION_MODE=async")
        if self.hsts_max_age_seconds < 0:
            raise ValueError("HSTS_MAX_AGE_SECONDS must be >= 0")


settings = Settings()
