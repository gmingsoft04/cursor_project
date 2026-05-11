"""Small utility helpers used across the package."""

from __future__ import annotations

import re
from urllib.parse import urlparse

COMPANY_SUFFIXES = (
    "inc",
    "inc.",
    "llc",
    "ltd",
    "ltd.",
    "limited",
    "gmbh",
    "sarl",
    "sas",
    "bv",
    "co",
    "co.",
    "company",
    "corp",
    "corp.",
    "corporation",
)


def extract_domain(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url if "://" in url else f"https://{url}")
    host = parsed.netloc.lower().split("@")[0].split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    return host or None


def clean_company_name(value: str) -> str:
    value = re.sub(r"\s+[-|:].*$", "", value).strip()
    value = re.sub(r"\b(official site|home|homepage)\b", "", value, flags=re.I).strip()
    return value or "Unknown Company"


def infer_company_name(title: str, url: str | None = None) -> str:
    cleaned = clean_company_name(title)
    if cleaned and len(cleaned) >= 2 and cleaned != "Unknown Company":
        return cleaned[:160]
    domain = extract_domain(url)
    if not domain:
        return title[:160] or "Unknown Company"
    return domain.split(".")[0].replace("-", " ").title()


def extract_linkedin_company_url(url: str | None) -> str | None:
    if not url or "linkedin.com/company" not in url:
        return None
    return url.split("?", 1)[0].rstrip("/")


def linkedin_vanity_from_url(url: str | None) -> str | None:
    if not url:
        return None
    match = re.search(r"linkedin\.com/company/([^/?#]+)", url)
    if not match:
        return None
    return match.group(1)


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        key = item.lower().strip()
        if key and key not in seen:
            seen.add(key)
            output.append(item)
    return output
