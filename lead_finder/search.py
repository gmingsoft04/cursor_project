"""搜索模块：基于关键词从 DuckDuckGo 收集候选 B2B 网站。

为什么用 DuckDuckGo：免 API key、对脚本相对友好、覆盖全球结果。
若被限流，会自动退避；也可换成 Bing/Google 自定义搜索（需 API key）。
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Iterable, Iterator
from urllib.parse import urlparse

import tldextract
from duckduckgo_search import DDGS
from tenacity import retry, stop_after_attempt, wait_exponential

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchHit:
    """单条搜索结果。"""

    title: str
    url: str
    snippet: str
    query: str

    @property
    def domain(self) -> str:
        ext = tldextract.extract(self.url)
        return ".".join(p for p in (ext.domain, ext.suffix) if p)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=20))
def _ddg_search(query: str, max_results: int, region: str) -> list[dict]:
    with DDGS() as ddgs:
        return list(ddgs.text(query, region=region, safesearch="moderate", max_results=max_results))


def search_queries(
    queries: Iterable[str],
    *,
    max_results_per_query: int = 25,
    regions: Iterable[str] = ("us-en", "uk-en", "de-de"),
    pause_seconds: float = 2.0,
) -> Iterator[SearchHit]:
    """对每条 query × 每个 region 调一次搜索，去重后逐条产出。

    - 跳过明显的搜索引擎 / 社媒 / 目录站结果（在抓取阶段再细过滤）。
    - regions 用 DDG 的区域代码：us-en, uk-en, de-de, fr-fr, ca-en, au-en …
    """
    seen: set[str] = set()
    for query in queries:
        for region in regions:
            log.info("Searching: %r [region=%s]", query, region)
            try:
                results = _ddg_search(query, max_results_per_query, region)
            except Exception as exc:
                log.warning("Search failed for %r/%s: %s", query, region, exc)
                continue

            for r in results:
                url = r.get("href") or r.get("url") or ""
                if not url:
                    continue
                host = urlparse(url).netloc.lower()
                if not host:
                    continue
                if host in seen:
                    continue
                seen.add(host)
                yield SearchHit(
                    title=r.get("title", ""),
                    url=url,
                    snippet=r.get("body", ""),
                    query=query,
                )
            time.sleep(pause_seconds)
