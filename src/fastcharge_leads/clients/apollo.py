"""Apollo.io enrichment integration."""

from __future__ import annotations

from typing import Any

from .http import JsonHttpClient
from ..models import ContactLead


class ApolloClient:
    def __init__(self, api_key: str, api_base: str = "https://api.apollo.io/v1", http: JsonHttpClient | None = None) -> None:
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.http = http or JsonHttpClient()

    def people_search(
        self,
        *,
        organization_domains: list[str] | None = None,
        keywords: str | None = None,
        titles: list[str] | None = None,
        country: str | None = None,
        page: int = 1,
        per_page: int = 10,
    ) -> list[ContactLead]:
        payload: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
            "q_keywords": keywords,
            "organization_domains": organization_domains,
            "person_titles": titles,
            "person_locations": [country] if country else None,
        }
        payload = {key: value for key, value in payload.items() if value}
        data = self.http.request_json(
            "POST",
            f"{self.api_base}/mixed_people/search",
            headers={"Cache-Control": "no-cache", "X-Api-Key": self.api_key, "Content-Type": "application/json"},
            json_body=payload,
        )
        people = data.get("people") or data.get("contacts") or []
        return [self._to_contact(person) for person in people if isinstance(person, dict)]

    def _to_contact(self, person: dict[str, Any]) -> ContactLead:
        organization = person.get("organization") or {}
        full_name = " ".join(part for part in [str(person.get("first_name") or "").strip(), str(person.get("last_name") or "").strip()] if part)
        if not full_name:
            full_name = str(person.get("name") or "Unknown Contact")
        return ContactLead(
            full_name=full_name,
            title=person.get("title"),
            email=person.get("email"),
            phone=person.get("phone") or person.get("sanitized_phone"),
            linkedin_url=person.get("linkedin_url"),
            company=organization.get("name") or person.get("organization_name"),
            country=person.get("country") or organization.get("country"),
            source="apollo",
            seniority=person.get("seniority"),
            confidence=_safe_float(person.get("email_confidence")),
            metadata=person,
        )


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
