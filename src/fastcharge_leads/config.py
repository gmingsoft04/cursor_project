"""Configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    serper_api_key: str | None = None
    apollo_api_key: str | None = None
    apollo_api_base: str = "https://api.apollo.io/v1"
    linkedin_access_token: str | None = None
    linkedin_api_base: str = "https://api.linkedin.com/v2"
    customs_api_base: str | None = None
    customs_api_key: str | None = None
    customs_import_endpoint: str = "/import-records"
    leads_db_path: str = "fastcharge_leads.sqlite3"
    request_timeout_seconds: float = 20.0

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            serper_api_key=_empty_to_none(os.getenv("SERPER_API_KEY")),
            apollo_api_key=_empty_to_none(os.getenv("APOLLO_API_KEY")),
            apollo_api_base=os.getenv("APOLLO_API_BASE", cls.apollo_api_base),
            linkedin_access_token=_empty_to_none(os.getenv("LINKEDIN_ACCESS_TOKEN")),
            linkedin_api_base=os.getenv("LINKEDIN_API_BASE", cls.linkedin_api_base),
            customs_api_base=_empty_to_none(os.getenv("CUSTOMS_API_BASE")),
            customs_api_key=_empty_to_none(os.getenv("CUSTOMS_API_KEY")),
            customs_import_endpoint=os.getenv("CUSTOMS_IMPORT_ENDPOINT", cls.customs_import_endpoint),
            leads_db_path=os.getenv("LEADS_DB_PATH", cls.leads_db_path),
            request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", cls.request_timeout_seconds)),
        )


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None
