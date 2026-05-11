"""LinkedIn official API integration.

LinkedIn API permissions vary by application. This adapter only calls official REST
endpoints when a token is supplied; it does not scrape LinkedIn pages.
"""

from __future__ import annotations

from typing import Any

from .http import JsonHttpClient


class LinkedInClient:
    def __init__(self, access_token: str, api_base: str = "https://api.linkedin.com/v2", http: JsonHttpClient | None = None) -> None:
        self.access_token = access_token
        self.api_base = api_base.rstrip("/")
        self.http = http or JsonHttpClient()

    def organization_by_vanity(self, vanity_name: str) -> dict[str, Any] | None:
        if not vanity_name:
            return None
        data = self.http.request_json(
            "GET",
            f"{self.api_base}/organizations",
            headers={"Authorization": f"Bearer {self.access_token}", "LinkedIn-Version": "202405"},
            query={"q": "vanityName", "vanityName": vanity_name},
        )
        elements = data.get("elements") or []
        if not elements:
            return None
        first = elements[0]
        return first if isinstance(first, dict) else None
