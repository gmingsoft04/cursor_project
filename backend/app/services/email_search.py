"""客户邮箱搜索服务

支持多提供方：
- hunter   : Hunter.io（商业），按域名搜索企业邮箱
- serpapi  : SerpAPI（商业），通过关键字搜索找到公司域名，再通过 Hunter 获取邮箱
- demo     : 演示模式，无需 API key，生成示例数据用于本地体验

关键字 -> 域名 -> 邮箱 是外贸开发的常见链路。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

import httpx

from ..config import get_settings


DOMAIN_RE = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)


@dataclass
class FoundEmail:
    email: str
    name: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    confidence: Optional[int] = None
    source: str = "unknown"
    keyword: Optional[str] = None


@dataclass
class SearchOutput:
    provider: str
    keyword: str
    items: List[FoundEmail] = field(default_factory=list)
    notice: Optional[str] = None


def _looks_like_domain(text: str) -> bool:
    text = text.strip().lower()
    if text.startswith("http"):
        try:
            host = urlparse(text).netloc
            return bool(DOMAIN_RE.match(host))
        except Exception:
            return False
    return bool(DOMAIN_RE.match(text))


def _extract_domain(text: str) -> str:
    text = text.strip().lower()
    if text.startswith("http"):
        host = urlparse(text).netloc
        return host or text
    return text


class HunterClient:
    """Hunter.io 域名邮箱搜索客户端"""

    BASE = "https://api.hunter.io/v2"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def domain_search(self, domain: str, limit: int = 20) -> List[FoundEmail]:
        url = f"{self.BASE}/domain-search"
        params = {"domain": domain, "api_key": self.api_key, "limit": limit}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json().get("data") or {}
        company = data.get("organization")
        country = data.get("country")
        website = data.get("domain")
        results: List[FoundEmail] = []
        for e in data.get("emails", []) or []:
            results.append(
                FoundEmail(
                    email=e.get("value"),
                    name=" ".join(filter(None, [e.get("first_name"), e.get("last_name")])) or None,
                    company=company,
                    position=e.get("position"),
                    country=country,
                    website=f"https://{website}" if website else None,
                    confidence=e.get("confidence"),
                    source="hunter",
                )
            )
        return results


class SerpApiClient:
    """SerpAPI：关键字 -> 公司域名"""

    BASE = "https://serpapi.com/search.json"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search_domains(self, keyword: str, limit: int = 10) -> List[str]:
        params = {"q": keyword, "engine": "google", "api_key": self.api_key, "num": limit}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(self.BASE, params=params)
            resp.raise_for_status()
            data = resp.json()
        domains: List[str] = []
        seen = set()
        for item in (data.get("organic_results") or [])[:limit]:
            link = item.get("link") or ""
            try:
                host = urlparse(link).netloc.lower()
            except Exception:
                continue
            host = re.sub(r"^www\.", "", host)
            if host and host not in seen and DOMAIN_RE.match(host):
                seen.add(host)
                domains.append(host)
        return domains


class DemoProvider:
    """演示模式：无需 API key，给出 1-2 条假数据，方便本地体验流程"""

    SAMPLE_PEOPLE = [
        ("John Smith", "Sourcing Manager"),
        ("Maria Garcia", "Procurement Officer"),
        ("Ahmed Hassan", "Buyer"),
        ("Linda Brown", "Purchasing Director"),
    ]

    def search(self, keyword: str, limit: int = 5) -> List[FoundEmail]:
        keyword = (keyword or "").strip()
        slug = re.sub(r"[^a-z0-9]+", "", keyword.lower()) or "demo"
        results: List[FoundEmail] = []
        for i, (full_name, position) in enumerate(self.SAMPLE_PEOPLE[: max(1, min(limit, 4))]):
            first = full_name.split()[0].lower()
            domain = f"{slug[:12]}-co{i + 1}.example"
            results.append(
                FoundEmail(
                    email=f"{first}@{domain}",
                    name=full_name,
                    company=f"{keyword.title()} Co. #{i + 1}",
                    position=position,
                    country="Demo",
                    website=f"https://{domain}",
                    confidence=50,
                    source="demo",
                    keyword=keyword,
                )
            )
        return results


class EmailSearchService:
    def __init__(self):
        self.settings = get_settings()
        self.hunter = HunterClient(self.settings.hunter_api_key) if self.settings.hunter_api_key else None
        self.serpapi = SerpApiClient(self.settings.serpapi_key) if self.settings.serpapi_key else None
        self.demo = DemoProvider()

    def available_providers(self) -> List[str]:
        out = []
        if self.hunter:
            out.append("hunter")
        if self.serpapi:
            out.append("serpapi")
        out.append("demo")
        return out

    def _pick_provider(self, requested: Optional[str], keyword: str) -> str:
        if requested:
            return requested
        is_domain = _looks_like_domain(keyword)
        for p in self.settings.providers:
            if p == "hunter" and self.hunter and is_domain:
                return p
            if p == "serpapi" and self.serpapi and self.hunter and not is_domain:
                return p
            if p == "hunter" and self.hunter and not is_domain:
                # 没有 serpapi 时，hunter 也支持公司名作为参数
                return p
            if p == "demo":
                return p
        return "demo"

    async def search(self, keyword: str, provider: Optional[str] = None, limit: int = 20) -> SearchOutput:
        keyword = (keyword or "").strip()
        if not keyword:
            return SearchOutput(provider="none", keyword=keyword, notice="关键字不能为空")

        chosen = self._pick_provider(provider, keyword)
        notice: Optional[str] = None
        items: List[FoundEmail] = []

        if chosen == "hunter":
            if not self.hunter:
                return SearchOutput(provider="hunter", keyword=keyword, notice="未配置 HUNTER_API_KEY")
            domain = _extract_domain(keyword) if _looks_like_domain(keyword) else None
            if domain:
                items = await self.hunter.domain_search(domain, limit=limit)
            else:
                # 当输入是公司名时，Hunter 也支持 company 参数
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.get(
                        f"{self.hunter.BASE}/domain-search",
                        params={"company": keyword, "api_key": self.hunter.api_key, "limit": limit},
                    )
                    resp.raise_for_status()
                    data = resp.json().get("data") or {}
                company = data.get("organization") or keyword
                website = data.get("domain")
                country = data.get("country")
                for e in data.get("emails", []) or []:
                    items.append(
                        FoundEmail(
                            email=e.get("value"),
                            name=" ".join(filter(None, [e.get("first_name"), e.get("last_name")])) or None,
                            company=company,
                            position=e.get("position"),
                            country=country,
                            website=f"https://{website}" if website else None,
                            confidence=e.get("confidence"),
                            source="hunter",
                            keyword=keyword,
                        )
                    )
            for it in items:
                it.keyword = keyword

        elif chosen == "serpapi":
            if not self.serpapi or not self.hunter:
                return SearchOutput(
                    provider="serpapi",
                    keyword=keyword,
                    notice="serpapi 模式需要同时配置 SERPAPI_KEY 与 HUNTER_API_KEY",
                )
            domains = await self.serpapi.search_domains(keyword, limit=min(8, max(3, limit // 3)))
            seen_emails = set()
            for d in domains:
                try:
                    found = await self.hunter.domain_search(d, limit=5)
                except httpx.HTTPError:
                    continue
                for it in found:
                    if it.email in seen_emails:
                        continue
                    seen_emails.add(it.email)
                    it.keyword = keyword
                    items.append(it)
                if len(items) >= limit:
                    break

        elif chosen == "demo":
            items = self.demo.search(keyword, limit=limit)
            notice = "当前为演示模式（未配置真实 API key）。生成的邮箱仅用于体验流程，请勿真实发送。"

        else:
            return SearchOutput(provider=chosen, keyword=keyword, notice=f"未知提供方: {chosen}")

        return SearchOutput(provider=chosen, keyword=keyword, items=items, notice=notice)
