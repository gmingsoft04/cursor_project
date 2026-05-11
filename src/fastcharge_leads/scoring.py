"""Lead scoring heuristics for fast charger and cable buyers."""

from __future__ import annotations

from .models import CompanyLead

PRODUCT_TERMS = (
    "gan",
    "pd charger",
    "fast charger",
    "usb-c",
    "type-c",
    "charging cable",
    "mobile accessories",
    "phone accessories",
)

BUYER_TERMS = (
    "importer",
    "distributor",
    "wholesale",
    "retailer",
    "procurement",
    "sourcing",
    "buyer",
)


def score_company(lead: CompanyLead) -> int:
    score = 0
    text = " ".join([lead.company_name, lead.product_interest or "", " ".join(lead.signals)]).lower()
    if lead.website or lead.domain:
        score += 10
    if lead.linkedin_url:
        score += 10
    if lead.customs_matches:
        score += min(30, 12 + lead.customs_matches * 4)
    if lead.contacts:
        score += min(25, 10 + len(lead.contacts) * 5)
        if any(contact.email for contact in lead.contacts):
            score += 10
    if any(term in text for term in PRODUCT_TERMS):
        score += 15
    if any(term in text for term in BUYER_TERMS):
        score += 10
    if lead.country:
        score += 5
    return min(score, 100)
