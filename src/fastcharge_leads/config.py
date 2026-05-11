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
