"""Minimal JSON HTTP client built on the Python standard library."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class HttpClientError(RuntimeError):
    """Raised when an HTTP request fails."""


class JsonHttpClient:
    def __init__(self, timeout_seconds: float = 20.0) -> None:
        self.timeout_seconds = timeout_seconds

    def request_json(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        query: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if query:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{urlencode(_strip_none(query), doseq=True)}"
        body = None
        request_headers = {"Accept": "application/json", **(headers or {})}
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")
        request = Request(url, data=body, headers=request_headers, method=method.upper())
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise HttpClientError(f"{method.upper()} {url} failed with HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise HttpClientError(f"{method.upper()} {url} failed: {exc.reason}") from exc
        if not payload:
            return {}
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise HttpClientError(f"{method.upper()} {url} returned invalid JSON") from exc
        if not isinstance(parsed, dict):
            return {"data": parsed}
        return parsed


def _strip_none(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}
