from __future__ import annotations

from pydantic import AliasChoices, Field
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


settings = Settings()
