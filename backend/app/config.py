from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "外贸客户开发系统"
    app_base_url: str = "http://127.0.0.1:8000"
    secret_key: str = "dev-secret-key-change-me"

    database_url: str = "sqlite:///./data/app.db"

    hunter_api_key: str = ""
    serpapi_key: str = ""
    search_providers: str = "hunter,serpapi,demo"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    smtp_from_name: str = ""
    smtp_from_email: str = ""

    send_batch_interval: float = 2.0

    @property
    def providers(self) -> List[str]:
        return [p.strip() for p in self.search_providers.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
