from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(..., alias="DATABASE_URL")
    jwt_secret_key: str = Field("change-me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    rate_limit_enabled: bool = Field(True, alias="RATE_LIMIT_ENABLED")
    rate_limit_default: str = Field("100/minute", alias="RATE_LIMIT_DEFAULT")
    rate_limit_auth: str = Field("10/minute", alias="RATE_LIMIT_AUTH")
    redis_url: str | None = Field(None, alias="REDIS_URL")
    environment: str = Field("development", alias="ENV")

    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    def validate_security(self) -> None:
        if self.is_production() and self.jwt_secret_key == "change-me":
            raise ValueError("JWT_SECRET_KEY must be set in production")


settings = Settings()
