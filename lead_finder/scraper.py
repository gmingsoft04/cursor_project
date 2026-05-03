"""网站抓取：从首页 + 联系页中提取公开的 B2B 邮箱。

设计要点
--------
1. 仅抓取**公开发布在企业网站联系页面**的邮箱（info@、sales@ 等业务邮箱）。
2. 遵守 robots.txt：默认尊重；可由调用方关闭，但不建议。
3. 处理常见的反混淆：`name [at] domain [dot] com`、`&#64;`、`(at)`、JS 拼接的少量场景。
4. 不解析登录后页面，不绕过验证码。
"""

from __future__ import annotations

import html
import logging
import re
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
import tldextract
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

log = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (compatible; LeadFinderBot/0.1; "
    "+https://example.com/bot) — research only, respects robots.txt"
)

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "en-US,en;q=0.9",
}

CONTACT_PATH_HINTS = (
    "contact", "contacts", "contact-us", "contactus", "about", "about-us",
    "kontakt", "impressum", "wholesale", "b2b", "trade", "support",
    "customer-service", "help",
)

EMAIL_RE = re.compile(
    r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
)

# 简易反混淆：name [at] domain [dot] com / name (at) domain (dot) com
DEOBF_RE = re.compile(
    r"([A-Za-z0-9._%+\-]+)\s*[\[\(\{]?\s*(?:at|@)\s*[\]\)\}]?\s*"
    r"([A-Za-z0-9\-]+(?:\s*[\[\(\{]?\s*(?:dot|\.)\s*[\]\)\}]?\s*[A-Za-z0-9\-]+)+)",
    re.IGNORECASE,
)


@dataclass
class Lead:
    """一条潜在客户记录。"""

    company: str
    domain: str
    email: str
    source_url: str
    country_hint: str
    score: int
    snippet: str


def _can_fetch(url: str, *, respect_robots: bool) -> bool:
    if not respect_robots:
        return True
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        # robots.txt 取不到时放行，但仍只抓公开 HTML
        return True


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=8))
def _get(url: str, timeout: int = 15) -> requests.Response | None:
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=True)
    except requests.RequestException as exc:
        log.debug("GET %s failed: %s", url, exc)
        return None
    if resp.status_code >= 400:
        return None
    if "text/html" not in resp.headers.get("Content-Type", "").lower():
        return None
    return resp


def _normalize_emails(text: str) -> set[str]:
    text = html.unescape(text)
    # 替换常见反混淆形式
    text = re.sub(r"\s*\[\s*at\s*\]\s*", "@", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\(\s*at\s*\)\s*", "@", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+at\s+", "@", text)
    text = re.sub(r"\s*\[\s*dot\s*\]\s*", ".", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\(\s*dot\s*\)\s*", ".", text, flags=re.IGNORECASE)

    found: set[str] = set()
    for m in EMAIL_RE.finditer(text):
        email = m.group(0).strip(".,;:'\"<>()[]{}").lower()
        # 过滤明显的图片资源/版本号尾巴
        if email.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
            continue
        found.add(email)
    return found


def _collect_contact_links(base_url: str, soup: BeautifulSoup) -> list[str]:
    out: list[str] = []
    base_host = urlparse(base_url).netloc
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue
        full = urljoin(base_url, href)
        host = urlparse(full).netloc
        if host != base_host:
            continue
        path = urlparse(full).path.lower()
        if any(hint in path for hint in CONTACT_PATH_HINTS):
            out.append(full)
    seen: set[str] = set()
    deduped: list[str] = []
    for u in out:
        if u in seen:
            continue
        seen.add(u)
        deduped.append(u)
    return deduped[:5]


def _country_hint_from_tld(domain: str) -> str:
    ext = tldextract.extract(domain)
    suffix = (ext.suffix or "").lower()
    mapping = {
        "us": "US", "uk": "UK", "co.uk": "UK", "de": "DE", "fr": "FR",
        "it": "IT", "es": "ES", "nl": "NL", "se": "SE", "ca": "CA",
        "au": "AU", "com.au": "AU", "ie": "IE", "be": "BE", "ch": "CH",
        "at": "AT", "dk": "DK", "no": "NO", "fi": "FI", "pl": "PL",
        "cz": "CZ", "pt": "PT",
    }
    return mapping.get(suffix, "")


def _score_email(
    email: str,
    *,
    site_domain: str,
    preferred_prefixes: Iterable[str],
    country_hint: str,
    snippet: str,
) -> int:
    score = 0
    local, _, domain = email.partition("@")
    # 1) 邮箱域 == 网站域 → 高度可信
    if domain.endswith(site_domain):
        score += 40
    # 2) B2B 前缀
    if any(local == p or local.startswith(p + ".") or local.startswith(p + "-") for p in preferred_prefixes):
        score += 25
    # 3) 国家匹配
    if country_hint in {"US", "UK", "DE", "FR", "IT", "ES", "NL", "SE", "CA", "AU", "IE", "BE", "CH", "AT", "DK", "NO", "FI", "PL", "CZ", "PT"}:
        score += 15
    # 4) 业务相关关键词
    keywords = ("charger", "cable", "usb", "gan", "accessor", "wholesale", "import", "distribut", "retail", "buyer", "purchas", "B2B")
    s = snippet.lower()
    if any(k.lower() in s for k in keywords):
        score += 10
    # 5) 个人邮箱（gmail/yahoo/outlook）通常不是采购对接邮箱
    if domain in {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com", "icloud.com", "qq.com", "163.com"}:
        score -= 20
    return score


def extract_leads(
    *,
    url: str,
    company_hint: str,
    snippet: str,
    preferred_prefixes: Iterable[str],
    blocklist_domains: set[str],
    blocklist_locals: set[str],
    respect_robots: bool = True,
) -> list[Lead]:
    """对一个候选网站抓取首页 + 联系页，返回评分后的 Lead 列表。"""
    if not _can_fetch(url, respect_robots=respect_robots):
        log.info("Blocked by robots.txt: %s", url)
        return []

    home = _get(url)
    if home is None:
        return []

    soup = BeautifulSoup(home.text, "lxml")
    pages = [(url, home.text)]
    for link in _collect_contact_links(home.url, soup):
        if not _can_fetch(link, respect_robots=respect_robots):
            continue
        sub = _get(link)
        if sub is not None:
            pages.append((sub.url, sub.text))

    site_domain_ext = tldextract.extract(home.url)
    site_domain = ".".join(p for p in (site_domain_ext.domain, site_domain_ext.suffix) if p)
    country_hint = _country_hint_from_tld(site_domain)

    # 公司名：优先 <title>，否则用 domain
    title_tag = soup.find("title")
    company = (title_tag.text.strip() if title_tag and title_tag.text else company_hint or site_domain)
    company = re.sub(r"\s+", " ", company)[:120]

    seen_emails: set[str] = set()
    leads: list[Lead] = []

    for source_url, html_text in pages:
        # 1) 取 mailto:
        sub_soup = BeautifulSoup(html_text, "lxml")
        mailto_emails: set[str] = set()
        for a in sub_soup.select("a[href^=mailto:]"):
            mailto = a["href"].split(":", 1)[1].split("?", 1)[0]
            mailto_emails.update(_normalize_emails(mailto))

        # 2) 反混淆扫描
        deobf_emails: set[str] = set()
        for m in DEOBF_RE.finditer(html_text):
            local = m.group(1)
            domain = re.sub(r"\s*[\[\(\{]?\s*(?:dot|\.)\s*[\]\)\}]?\s*", ".", m.group(2), flags=re.IGNORECASE)
            domain = re.sub(r"\s+", "", domain)
            candidate = f"{local}@{domain}".lower()
            if EMAIL_RE.fullmatch(candidate):
                deobf_emails.add(candidate)

        # 3) 普通正则扫描
        regex_emails = _normalize_emails(html_text)

        for email in mailto_emails | deobf_emails | regex_emails:
            local, _, domain = email.partition("@")
            if not domain:
                continue
            if domain in blocklist_domains:
                continue
            if local in blocklist_locals:
                continue
            if email in seen_emails:
                continue
            seen_emails.add(email)

            score = _score_email(
                email,
                site_domain=site_domain,
                preferred_prefixes=preferred_prefixes,
                country_hint=country_hint,
                snippet=f"{snippet} {company}",
            )
            leads.append(
                Lead(
                    company=company,
                    domain=site_domain,
                    email=email,
                    source_url=source_url,
                    country_hint=country_hint,
                    score=score,
                    snippet=snippet[:280],
                )
            )

    leads.sort(key=lambda l: l.score, reverse=True)
    return leads
