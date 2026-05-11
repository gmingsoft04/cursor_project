"""Serper.dev search integration."""

from __future__ import annotations

from typing import Any

from .http import JsonHttpClient
from ..models import SearchResult


class SerperClient:
    endpoint = "https://google.serper.dev/search"

    def __init__(self, api_key: str, http: JsonHttpClient | None = None) -> None:
        self.api_key = api_key
        self.http = http or JsonHttpClient()

    def search(self, query: str, *, country_code: str | None = None, limit: int = 10) -> list[SearchResult]:
        payload: dict[str, Any] = {"q": query, "num": limit}
        if country_code:
            payload["gl"] = country_code.lower()
        data = self.http.request_json(
            "POST",
            self.endpoint,
            headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
            json_body=payload,
        )
        results: list[SearchResult] = []
        for item in data.get("organic", [])[:limit]:
            results.append(
                SearchResult(
                    title=str(item.get("title") or ""),
                    url=str(item.get("link") or ""),
                    snippet=str(item.get("snippet") or ""),
                    source="serper",
                    metadata=item,
                )
            )
        return [result for result in results if result.title and result.url]
