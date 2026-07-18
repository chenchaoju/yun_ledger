from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "个人消费记录系统"
    environment: str = "development"
    api_prefix: str = "/api"
    secret_key: str = "change-this-secret-key"
    access_token_expire_minutes: int = 60 * 24 * 7
    database_url: str = "mysql+pymysql://root:root@127.0.0.1:3306/finance_data?charset=utf8mb4"
    cors_origins: str = "http://localhost:8023,http://127.0.0.1:8023,http://localhost:5173,http://127.0.0.1:5173"
    cors_origin_regex: str | None = (
        r"^http://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|"
        r"172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)(:\d+)?$"
    )

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
