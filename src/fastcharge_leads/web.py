"""JSON API server for the separated Vue dashboard."""

from __future__ import annotations

import json
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from .clients.ai import LocalTemplateEmailGenerator, OpenAICompatibleEmailGenerator
from .clients.email_sender import SmtpConfig, SmtpEmailSender
from .clients.http import JsonHttpClient
from .config import Settings
from .email_outreach import OutreachWorkflow
from .store import LeadStore


@dataclass(frozen=True, slots=True)
class ApiResponse:
    status: int
    body: dict[str, Any] | list[Any] | None = None
    content_type: str = "application/json; charset=utf-8"
    headers: dict[str, str] | None = None


class WebApi:
    def __init__(self, *, db_path: str, settings: Settings) -> None:
        self.db_path = db_path
        self.settings = settings

    def dispatch(self, method: str, raw_path: str, body: bytes = b"") -> ApiResponse:
        parsed = urlparse(raw_path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        payload = _json_body(body)
        try:
            if method == "OPTIONS":
                return ApiResponse(status=204)
            if method == "GET":
                return self._get(path, query)
            if method == "POST":
                return self._post(path, payload)
            if method == "PUT":
                return self._put(path, payload)
            return _error("Unsupported method.", status=405)
        except ValueError as exc:
            return _error(str(exc), status=400)
        except Exception as exc:  # pragma: no cover - keeps API callers from receiving empty responses.
            return _error(str(exc), status=500)

    def _get(self, path: str, query: dict[str, list[str]]) -> ApiResponse:
        if path in {"/", "/api/health"}:
            return _json({"status": "ok", "service": "fastcharge-leads-api"})
        if path == "/api/dashboard":
            return self._dashboard()
        if path == "/api/leads":
            return self._leads(query)
        if path == "/api/email-drafts":
            return self._email_drafts(query)
        if path.startswith("/api/email-drafts/"):
            return self._email_detail(_path_int(path, "/api/email-drafts/"))
        return _error("Not found.", status=404)

    def _post(self, path: str, payload: dict[str, Any]) -> ApiResponse:
        if path == "/api/email-drafts/generate":
            return self._generate_email_drafts(payload)
        if path == "/api/email-drafts/send-approved":
            return self._send_approved(payload)
        if path.startswith("/api/email-drafts/"):
            remainder = path.removeprefix("/api/email-drafts/")
            draft_id_text, _, action = remainder.partition("/")
            draft_id = int(draft_id_text)
            if action == "approve":
                return self._review_email(draft_id, approved=True, payload=payload)
            if action == "reject":
                return self._review_email(draft_id, approved=False, payload=payload)
        return _error("Action not found.", status=404)

    def _put(self, path: str, payload: dict[str, Any]) -> ApiResponse:
        if path.startswith("/api/email-drafts/"):
            return self._edit_email(_path_int(path, "/api/email-drafts/"), payload)
        return _error("Action not found.", status=404)

    def _dashboard(self) -> ApiResponse:
        with _store(self.db_path) as store:
            companies = store.list_companies(limit=5)
            draft_counts = _draft_counts(store)
        return _json({"top_leads": [_company_payload(row) for row in companies], "draft_counts": draft_counts})

    def _leads(self, query: dict[str, list[str]]) -> ApiResponse:
        limit = _int_query(query, "limit", 100)
        with _store(self.db_path) as store:
            rows = store.list_companies(limit=limit)
        return _json({"items": [_company_payload(row) for row in rows]})

    def _email_drafts(self, query: dict[str, list[str]]) -> ApiResponse:
        status = _one(query, "status") or None
        limit = _int_query(query, "limit", 50)
        with _store(self.db_path) as store:
            drafts = store.list_email_drafts(status=status, limit=limit)
            draft_counts = _draft_counts(store)
        return _json({"items": [_draft_payload(row) for row in drafts], "draft_counts": draft_counts})

    def _email_detail(self, draft_id: int) -> ApiResponse:
        with _store(self.db_path) as store:
            draft = store.get_email_draft(draft_id)
        if not draft:
            return _error("Draft not found.", status=404)
        return _json(_draft_payload(draft, include_body=True))

    def _generate_email_drafts(self, payload: dict[str, Any]) -> ApiResponse:
        limit = int(payload.get("limit") or 20)
        min_score = int(payload.get("min_score") or 70)
        language = str(payload.get("language") or "English")
        with _store(self.db_path) as store:
            result = OutreachWorkflow(store=store, generator=self._generator()).generate_drafts(
                limit=limit,
                min_score=min_score,
                language=language,
            )
        return _json(result.as_dict(), status=201)

    def _edit_email(self, draft_id: int, payload: dict[str, Any]) -> ApiResponse:
        subject = str(payload.get("subject") or "").strip()
        body = str(payload.get("body") or "").strip()
        if not subject or not body:
            raise ValueError("Subject and body are required.")
        with _store(self.db_path) as store:
            store.update_email_draft_content(draft_id, subject=subject, body=body)
            draft = store.get_email_draft(draft_id)
        if not draft:
            return _error("Draft not found.", status=404)
        return _json(_draft_payload(draft, include_body=True))

    def _review_email(self, draft_id: int, *, approved: bool, payload: dict[str, Any]) -> ApiResponse:
        reviewer = str(payload.get("reviewer") or "vue-dashboard")
        with _store(self.db_path) as store:
            store.review_email_draft(draft_id, approved=approved, reviewer=reviewer)
            draft = store.get_email_draft(draft_id)
        if not draft:
            return _error("Draft not found.", status=404)
        return _json(_draft_payload(draft, include_body=True))

    def _send_approved(self, payload: dict[str, Any]) -> ApiResponse:
        limit = int(payload.get("limit") or 20)
        dry_run = bool(payload.get("dry_run", False))
        with _store(self.db_path) as store:
            result = OutreachWorkflow(store=store, generator=LocalTemplateEmailGenerator()).send_approved(
                sender=self._sender(),
                limit=limit,
                dry_run=dry_run,
            )
        return _json(result.as_dict())

    def _generator(self):
        http = JsonHttpClient(self.settings.request_timeout_seconds)
        if self.settings.ai_api_key:
            return OpenAICompatibleEmailGenerator(
                api_key=self.settings.ai_api_key,
                api_base=self.settings.ai_api_base,
                model=self.settings.ai_model,
                http=http,
            )
        return LocalTemplateEmailGenerator()

    def _sender(self) -> SmtpEmailSender:
        return SmtpEmailSender(
            SmtpConfig(
                host=self.settings.smtp_host or "",
                port=self.settings.smtp_port,
                username=self.settings.smtp_username,
                password=self.settings.smtp_password,
                from_email=self.settings.smtp_from_email,
                from_name=self.settings.smtp_from_name,
                use_tls=self.settings.smtp_use_tls,
            )
        )


def run_web_server(*, db_path: str, settings: Settings, host: str = "127.0.0.1", port: int = 8080) -> None:
    api = WebApi(db_path=db_path, settings=settings)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - standard library handler API.
            _send(self, api.dispatch("GET", self.path))

        def do_POST(self) -> None:  # noqa: N802 - standard library handler API.
            length = int(self.headers.get("Content-Length", "0"))
            _send(self, api.dispatch("POST", self.path, self.rfile.read(length)))

        def do_PUT(self) -> None:  # noqa: N802 - standard library handler API.
            length = int(self.headers.get("Content-Length", "0"))
            _send(self, api.dispatch("PUT", self.path, self.rfile.read(length)))

        def do_OPTIONS(self) -> None:  # noqa: N802 - standard library handler API.
            _send(self, api.dispatch("OPTIONS", self.path))

        def log_message(self, format: str, *args) -> None:  # noqa: A002 - standard library signature.
            return

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"FastCharge Leads API running at http://{host}:{port}")
    server.serve_forever()


def _send(handler: BaseHTTPRequestHandler, response: ApiResponse) -> None:
    handler.send_response(response.status)
    handler.send_header("Content-Type", response.content_type)
    for key, value in _headers(response).items():
        handler.send_header(key, value)
    handler.end_headers()
    if response.body is not None:
        handler.wfile.write(json.dumps(response.body, ensure_ascii=False, default=str).encode("utf-8"))


def _headers(response: ApiResponse) -> dict[str, str]:
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,POST,PUT,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        **(response.headers or {}),
    }


class _store:
    def __init__(self, path: str) -> None:
        self.store = LeadStore(path)

    def __enter__(self) -> LeadStore:
        return self.store

    def __exit__(self, *args) -> None:
        self.store.close()


def _draft_counts(store: LeadStore) -> dict[str, int]:
    counts = {status: 0 for status in ["draft", "approved", "rejected", "sent", "failed"]}
    for row in store.list_email_drafts(limit=10000):
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return counts


def _company_payload(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "company_name": row["company_name"],
        "website": row["website"],
        "domain": row["domain"],
        "country": row["country"],
        "source": row["source"],
        "product_interest": row["product_interest"],
        "linkedin_url": row["linkedin_url"],
        "customs_matches": row["customs_matches"],
        "score": row["score"],
        "signals": json.loads(row["signals_json"] or "[]"),
        "contact_count": row["contact_count"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _draft_payload(row: Any, *, include_body: bool = False) -> dict[str, Any]:
    payload = {
        "id": row["id"],
        "company_id": row["company_id"],
        "company_name": row["company_name"],
        "contact_id": row["contact_id"],
        "recipient_email": row["recipient_email"],
        "recipient_name": row["recipient_name"],
        "subject": row["subject"],
        "language": row["language"],
        "model": row["model"],
        "status": row["status"],
        "reviewed_by": row["reviewed_by"],
        "reviewed_at": row["reviewed_at"],
        "sent_at": row["sent_at"],
        "error_message": row["error_message"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
    if include_body:
        payload["body"] = row["body"]
        payload["metadata"] = json.loads(row["metadata_json"] or "{}")
    return payload


def _json(body: dict[str, Any] | list[Any], *, status: int = 200) -> ApiResponse:
    return ApiResponse(status=status, body=body)


def _error(message: str, *, status: int) -> ApiResponse:
    return _json({"error": message}, status=status)


def _json_body(body: bytes) -> dict[str, Any]:
    if not body:
        return {}
    parsed = json.loads(body.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("Request JSON body must be an object.")
    return parsed


def _path_int(path: str, prefix: str) -> int:
    return int(path.removeprefix(prefix).split("/", 1)[0])


def _one(values: dict[str, list[str]], key: str) -> str:
    return values.get(key, [""])[0]


def _int_query(values: dict[str, list[str]], key: str, default: int) -> int:
    try:
        return int(_one(values, key) or default)
    except ValueError:
        return default
