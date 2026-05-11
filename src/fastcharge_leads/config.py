"""Configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_APOLLO_API_BASE = "https://api.apollo.io/v1"
DEFAULT_LINKEDIN_API_BASE = "https://api.linkedin.com/v2"
DEFAULT_CUSTOMS_IMPORT_ENDPOINT = "/import-records"
DEFAULT_LEADS_DB_PATH = "fastcharge_leads.sqlite3"
DEFAULT_REQUEST_TIMEOUT_SECONDS = 20.0
DEFAULT_AI_API_BASE = "https://api.openai.com/v1"
DEFAULT_AI_MODEL = "gpt-4o-mini"
DEFAULT_SMTP_PORT = 587
DEFAULT_SMTP_USE_TLS = True
DEFAULT_AUTH_ADMIN_USERNAME = "admin"
DEFAULT_AUTH_ADMIN_PASSWORD = "change-me"
DEFAULT_AUTH_SESSION_HOURS = 12
DEFAULT_CORS_ALLOW_ORIGIN = "*"


@dataclass(frozen=True, slots=True)
class Settings:
    serper_api_key: str | None = None
    apollo_api_key: str | None = None
    apollo_api_base: str = DEFAULT_APOLLO_API_BASE
    linkedin_access_token: str | None = None
    linkedin_api_base: str = DEFAULT_LINKEDIN_API_BASE
    customs_api_base: str | None = None
    customs_api_key: str | None = None
    customs_import_endpoint: str = DEFAULT_CUSTOMS_IMPORT_ENDPOINT
    leads_db_path: str = DEFAULT_LEADS_DB_PATH
    request_timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT_SECONDS
    ai_api_key: str | None = None
    ai_api_base: str = DEFAULT_AI_API_BASE
    ai_model: str = DEFAULT_AI_MODEL
    smtp_host: str | None = None
    smtp_port: int = DEFAULT_SMTP_PORT
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str | None = None
    smtp_use_tls: bool = DEFAULT_SMTP_USE_TLS
    auth_admin_username: str = DEFAULT_AUTH_ADMIN_USERNAME
    auth_admin_password: str = DEFAULT_AUTH_ADMIN_PASSWORD
    auth_session_hours: int = DEFAULT_AUTH_SESSION_HOURS
    cors_allow_origin: str = DEFAULT_CORS_ALLOW_ORIGIN

    @classmethod
    def from_env(cls) -> "Settings":
        _load_env_file()
        return cls(
            serper_api_key=_empty_to_none(os.getenv("SERPER_API_KEY")),
            apollo_api_key=_empty_to_none(os.getenv("APOLLO_API_KEY")),
            apollo_api_base=os.getenv("APOLLO_API_BASE", DEFAULT_APOLLO_API_BASE),
            linkedin_access_token=_empty_to_none(os.getenv("LINKEDIN_ACCESS_TOKEN")),
            linkedin_api_base=os.getenv("LINKEDIN_API_BASE", DEFAULT_LINKEDIN_API_BASE),
            customs_api_base=_empty_to_none(os.getenv("CUSTOMS_API_BASE")),
            customs_api_key=_empty_to_none(os.getenv("CUSTOMS_API_KEY")),
            customs_import_endpoint=os.getenv("CUSTOMS_IMPORT_ENDPOINT", DEFAULT_CUSTOMS_IMPORT_ENDPOINT),
            leads_db_path=os.getenv("LEADS_DB_PATH", DEFAULT_LEADS_DB_PATH),
            request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", str(DEFAULT_REQUEST_TIMEOUT_SECONDS))),
            ai_api_key=_empty_to_none(os.getenv("AI_API_KEY")),
            ai_api_base=os.getenv("AI_API_BASE", DEFAULT_AI_API_BASE),
            ai_model=os.getenv("AI_MODEL", DEFAULT_AI_MODEL),
            smtp_host=_empty_to_none(os.getenv("SMTP_HOST")),
            smtp_port=int(os.getenv("SMTP_PORT", str(DEFAULT_SMTP_PORT))),
            smtp_username=_empty_to_none(os.getenv("SMTP_USERNAME")),
            smtp_password=_empty_to_none(os.getenv("SMTP_PASSWORD")),
            smtp_from_email=_empty_to_none(os.getenv("SMTP_FROM_EMAIL")),
            smtp_from_name=_empty_to_none(os.getenv("SMTP_FROM_NAME")),
            smtp_use_tls=_parse_bool(os.getenv("SMTP_USE_TLS"), DEFAULT_SMTP_USE_TLS),
            auth_admin_username=os.getenv("AUTH_ADMIN_USERNAME", DEFAULT_AUTH_ADMIN_USERNAME),
            auth_admin_password=os.getenv("AUTH_ADMIN_PASSWORD", DEFAULT_AUTH_ADMIN_PASSWORD),
            auth_session_hours=int(os.getenv("AUTH_SESSION_HOURS", str(DEFAULT_AUTH_SESSION_HOURS))),
            cors_allow_origin=os.getenv("CORS_ALLOW_ORIGIN", DEFAULT_CORS_ALLOW_ORIGIN),
        )


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _load_env_file(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
