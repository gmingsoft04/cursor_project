"""Shared domain models for the lead generation pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    source: str = "serper"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CustomsRecord:
    importer_name: str
    product_description: str
    country: str | None = None
    exporter_name: str | None = None
    hs_code: str | None = None
    shipment_date: str | None = None
    source: str = "customs"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ContactLead:
    full_name: str
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    company: str | None = None
    country: str | None = None
    source: str = "apollo"
    seniority: str | None = None
    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CompanyLead:
    company_name: str
    website: str | None = None
    domain: str | None = None
    country: str | None = None
    source: str = "pipeline"
    product_interest: str | None = None
    linkedin_url: str | None = None
    apollo_id: str | None = None
    customs_matches: int = 0
    contacts: list[ContactLead] = field(default_factory=list)
    signals: list[str] = field(default_factory=list)
    score: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def fingerprint(self) -> str:
        if self.domain:
            return self.domain.lower().strip()
        return normalize_company_name(self.company_name)


def normalize_company_name(name: str) -> str:
    return " ".join(name.lower().replace("&", "and").split())


@dataclass(slots=True)
class EmailDraft:
    company_id: int
    recipient_email: str
    subject: str
    body: str
    contact_id: int | None = None
    recipient_name: str | None = None
    language: str = "English"
    model: str | None = None
    status: str = "draft"
    metadata: dict[str, Any] = field(default_factory=dict)
