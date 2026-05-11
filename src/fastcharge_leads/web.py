"""JSON API server for the separated Vue dashboard."""

from __future__ import annotations

import json
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
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

    def dispatch(self, method: str, raw_path: str, body: bytes = b"", headers: dict[str, str] | None = None) -> ApiResponse:
        parsed = urlparse(raw_path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        payload = _json_body(body)
        headers = headers or {}
        try:
            if method == "OPTIONS":
                return ApiResponse(status=204)
            if method == "POST" and path == "/api/auth/login":
                return self._login(payload)
            actor = self._authenticate(headers, required=path not in {"/", "/api/health"})
            if actor is None and path not in {"/", "/api/health"}:
                return _error("Authentication required.", status=401)
            if method == "GET":
                return self._get(path, query, actor=actor)
            if method == "POST":
                return self._post(path, payload, actor=actor or "anonymous", headers=headers)
            if method == "PUT":
                return self._put(path, payload, actor=actor or "anonymous")
            if method == "DELETE":
                return self._delete(path, actor=actor or "anonymous")
            return _error("Unsupported method.", status=405)
        except ValueError as exc:
            return _error(str(exc), status=400)
        except Exception as exc:  # pragma: no cover - keeps API callers from receiving empty responses.
            return _error(str(exc), status=500)

    def _get(self, path: str, query: dict[str, list[str]], *, actor: str | None) -> ApiResponse:
        if path in {"/", "/api/health"}:
            return _json({"status": "ok", "service": "fastcharge-leads-api"})
        if path == "/api/auth/me":
            return _json({"username": actor, "role": "admin"})
        if path == "/api/dashboard":
            return self._dashboard()
        if path == "/api/leads":
            return self._leads(query)
        if path.startswith("/api/leads/"):
            return self._lead_detail(_path_int(path, "/api/leads/"))
        if path == "/api/audit-logs":
            return self._audit_logs(query)
        if path == "/api/suppressions":
            return self._suppressions(query)
        if path == "/api/email-drafts":
            return self._email_drafts(query)
        if path.startswith("/api/email-drafts/"):
            return self._email_detail(_path_int(path, "/api/email-drafts/"))
        return _error("Not found.", status=404)

    def _post(self, path: str, payload: dict[str, Any], *, actor: str, headers: dict[str, str]) -> ApiResponse:
        if path == "/api/auth/logout":
            return self._logout(headers, actor=actor)
        if path == "/api/email-drafts/generate":
            return self._generate_email_drafts(payload, actor=actor)
        if path == "/api/email-drafts/send-approved":
            return self._send_approved(payload, actor=actor)
        if path == "/api/suppressions":
            return self._add_suppression(payload, actor=actor)
        if path.startswith("/api/email-drafts/"):
            remainder = path.removeprefix("/api/email-drafts/")
            draft_id_text, _, action = remainder.partition("/")
            draft_id = int(draft_id_text)
            if action == "approve":
                return self._review_email(draft_id, approved=True, payload=payload, actor=actor)
            if action == "reject":
                return self._review_email(draft_id, approved=False, payload=payload, actor=actor)
        return _error("Action not found.", status=404)

    def _put(self, path: str, payload: dict[str, Any], *, actor: str) -> ApiResponse:
        if path.startswith("/api/leads/") and path.endswith("/crm"):
            company_id = int(path.removeprefix("/api/leads/").split("/", 1)[0])
            return self._update_company_crm(company_id, payload, actor=actor)
        if path.startswith("/api/email-drafts/"):
            return self._edit_email(_path_int(path, "/api/email-drafts/"), payload, actor=actor)
        return _error("Action not found.", status=404)

    def _delete(self, path: str, *, actor: str) -> ApiResponse:
        if path.startswith("/api/suppressions/"):
            suppression_id = _path_int(path, "/api/suppressions/")
            with _store(self.db_path) as store:
                store.delete_suppression(suppression_id)
                store.log_action(
                    actor=actor,
                    action="suppressions.delete",
                    entity_type="suppression",
                    entity_id=suppression_id,
                )
            return _json({"deleted": True})
        return _error("Action not found.", status=404)

    def _login(self, payload: dict[str, Any]) -> ApiResponse:
        username = str(payload.get("username") or "")
        password = str(payload.get("password") or "")
        if not (
            hmac.compare_digest(username, self.settings.auth_admin_username)
            and hmac.compare_digest(password, self.settings.auth_admin_password)
        ):
            with _store(self.db_path) as store:
                store.log_action(actor=username or "anonymous", action="auth.login_failed", metadata={"username": username})
            return _error("Invalid username or password.", status=401)
        token = secrets.token_urlsafe(32)
        expires_at = _utc_now() + timedelta(hours=self.settings.auth_session_hours)
        with _store(self.db_path) as store:
            store.create_session(
                token_hash=_token_hash(token),
                username=username,
                role="admin",
                expires_at=_format_time(expires_at),
            )
            store.log_action(actor=username, action="auth.login", metadata={"role": "admin"})
        return _json(
            {
                "token": token,
                "user": {"username": username, "role": "admin"},
                "expires_at": _format_time(expires_at),
            }
        )

    def _logout(self, headers: dict[str, str], *, actor: str) -> ApiResponse:
        token = _bearer_token(headers)
        if token:
            with _store(self.db_path) as store:
                store.delete_session(_token_hash(token))
                store.log_action(actor=actor, action="auth.logout")
        return _json({"status": "logged_out"})

    def _authenticate(self, headers: dict[str, str], *, required: bool) -> str | None:
        token = _bearer_token(headers)
        if not token:
            return None if required else None
        with _store(self.db_path) as store:
            session = store.get_session(_token_hash(token), now=_format_time(_utc_now()))
        if not session:
            return None
        return str(session["username"])

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

    def _lead_detail(self, company_id: int) -> ApiResponse:
        with _store(self.db_path) as store:
            company = store.get_company(company_id)
            if not company:
                return _error("Company not found.", status=404)
            contacts = store.list_contacts_for_company(company_id)
            drafts = store.list_company_email_drafts(company_id)
            logs = store.list_company_audit_logs(company_id, limit=100)
        return _json(
            {
                "company": _company_payload(company, contact_count=len(contacts)),
                "contacts": [_contact_payload(row) for row in contacts],
                "email_drafts": [_draft_payload(row) for row in drafts],
                "timeline": _timeline_payload(logs, drafts),
            }
        )

    def _audit_logs(self, query: dict[str, list[str]]) -> ApiResponse:
        limit = _int_query(query, "limit", 100)
        with _store(self.db_path) as store:
            rows = store.list_audit_logs(limit=limit)
        return _json({"items": [_audit_payload(row) for row in rows]})

    def _suppressions(self, query: dict[str, list[str]]) -> ApiResponse:
        limit = _int_query(query, "limit", 200)
        with _store(self.db_path) as store:
            rows = store.list_suppressions(limit=limit)
        return _json({"items": [_suppression_payload(row) for row in rows]})

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

    def _generate_email_drafts(self, payload: dict[str, Any], *, actor: str) -> ApiResponse:
        limit = int(payload.get("limit") or 20)
        min_score = int(payload.get("min_score") or 70)
        language = str(payload.get("language") or "English")
        with _store(self.db_path) as store:
            result = OutreachWorkflow(store=store, generator=self._generator()).generate_drafts(
                limit=limit,
                min_score=min_score,
                language=language,
            )
            store.log_action(
                actor=actor,
                action="email_drafts.generate",
                metadata={"created": result.created, "limit": limit, "min_score": min_score, "language": language},
            )
        return _json(result.as_dict(), status=201)

    def _edit_email(self, draft_id: int, payload: dict[str, Any], *, actor: str) -> ApiResponse:
        subject = str(payload.get("subject") or "").strip()
        body = str(payload.get("body") or "").strip()
        if not subject or not body:
            raise ValueError("Subject and body are required.")
        with _store(self.db_path) as store:
            store.update_email_draft_content(draft_id, subject=subject, body=body)
            store.log_action(actor=actor, action="email_drafts.edit", entity_type="email_draft", entity_id=draft_id)
            draft = store.get_email_draft(draft_id)
        if not draft:
            return _error("Draft not found.", status=404)
        return _json(_draft_payload(draft, include_body=True))

    def _review_email(self, draft_id: int, *, approved: bool, payload: dict[str, Any], actor: str) -> ApiResponse:
        reviewer = str(payload.get("reviewer") or "vue-dashboard")
        with _store(self.db_path) as store:
            store.review_email_draft(draft_id, approved=approved, reviewer=reviewer)
            store.log_action(
                actor=actor,
                action="email_drafts.approve" if approved else "email_drafts.reject",
                entity_type="email_draft",
                entity_id=draft_id,
                metadata={"reviewer": reviewer},
            )
            draft = store.get_email_draft(draft_id)
        if not draft:
            return _error("Draft not found.", status=404)
        return _json(_draft_payload(draft, include_body=True))

    def _send_approved(self, payload: dict[str, Any], *, actor: str) -> ApiResponse:
        limit = int(payload.get("limit") or 20)
        dry_run = bool(payload.get("dry_run", False))
        with _store(self.db_path) as store:
            result = OutreachWorkflow(store=store, generator=LocalTemplateEmailGenerator()).send_approved(
                sender=self._sender(),
                limit=limit,
                dry_run=dry_run,
            )
            store.log_action(
                actor=actor,
                action="email_drafts.send_approved_dry_run" if dry_run else "email_drafts.send_approved",
                metadata=result.as_dict(),
            )
        return _json(result.as_dict())

    def _add_suppression(self, payload: dict[str, Any], *, actor: str) -> ApiResponse:
        kind = str(payload.get("kind") or "").strip().lower()
        value = str(payload.get("value") or "").strip()
        reason = _empty_string_to_none(payload.get("reason"))
        if not kind or not value:
            raise ValueError("kind and value are required.")
        with _store(self.db_path) as store:
            suppression_id = store.add_suppression(kind=kind, value=value, reason=reason, created_by=actor)
            store.log_action(
                actor=actor,
                action="suppressions.add",
                entity_type="suppression",
                entity_id=suppression_id,
                metadata={"kind": kind, "value": value, "reason": reason},
            )
            created = store.get_suppression(suppression_id)
        return _json(_suppression_payload(created), status=201)

    def _update_company_crm(self, company_id: int, payload: dict[str, Any], *, actor: str) -> ApiResponse:
        crm_status = str(payload.get("crm_status") or "").strip()
        if not crm_status:
            raise ValueError("crm_status is required.")
        with _store(self.db_path) as store:
            store.update_company_crm(
                company_id,
                crm_status=crm_status,
                owner=_empty_string_to_none(payload.get("owner")),
                next_follow_up_at=_empty_string_to_none(payload.get("next_follow_up_at")),
                crm_notes=_empty_string_to_none(payload.get("crm_notes")),
            )
            store.log_action(
                actor=actor,
                action="companies.crm_update",
                entity_type="company",
                entity_id=company_id,
                metadata={
                    "crm_status": crm_status,
                    "owner": payload.get("owner"),
                    "next_follow_up_at": payload.get("next_follow_up_at"),
                },
            )
            company = store.get_company(company_id)
            contact_count = len(store.list_contacts_for_company(company_id))
        if not company:
            return _error("Company not found.", status=404)
        return _json(_company_payload(company, contact_count=contact_count))

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
            _send(self, api.dispatch("GET", self.path, headers=dict(self.headers)), api.settings.cors_allow_origin)

        def do_POST(self) -> None:  # noqa: N802 - standard library handler API.
            length = int(self.headers.get("Content-Length", "0"))
            _send(
                self,
                api.dispatch("POST", self.path, self.rfile.read(length), headers=dict(self.headers)),
                api.settings.cors_allow_origin,
            )

        def do_PUT(self) -> None:  # noqa: N802 - standard library handler API.
            length = int(self.headers.get("Content-Length", "0"))
            _send(
                self,
                api.dispatch("PUT", self.path, self.rfile.read(length), headers=dict(self.headers)),
                api.settings.cors_allow_origin,
            )

        def do_DELETE(self) -> None:  # noqa: N802 - standard library handler API.
            _send(self, api.dispatch("DELETE", self.path, headers=dict(self.headers)), api.settings.cors_allow_origin)

        def do_OPTIONS(self) -> None:  # noqa: N802 - standard library handler API.
            _send(self, api.dispatch("OPTIONS", self.path, headers=dict(self.headers)), api.settings.cors_allow_origin)

        def log_message(self, format: str, *args) -> None:  # noqa: A002 - standard library signature.
            return

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"FastCharge Leads API running at http://{host}:{port}")
    server.serve_forever()


def _send(handler: BaseHTTPRequestHandler, response: ApiResponse, cors_allow_origin: str) -> None:
    handler.send_response(response.status)
    handler.send_header("Content-Type", response.content_type)
    for key, value in _headers(response, cors_allow_origin).items():
        handler.send_header(key, value)
    handler.end_headers()
    if response.body is not None:
        handler.wfile.write(json.dumps(response.body, ensure_ascii=False, default=str).encode("utf-8"))


def _headers(response: ApiResponse, cors_allow_origin: str) -> dict[str, str]:
    return {
        "Access-Control-Allow-Origin": cors_allow_origin,
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
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


def _company_payload(row: Any, *, contact_count: int | None = None) -> dict[str, Any]:
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
        "contact_count": contact_count if contact_count is not None else row["contact_count"],
        "crm_status": row["crm_status"],
        "owner": row["owner"],
        "next_follow_up_at": row["next_follow_up_at"],
        "crm_notes": row["crm_notes"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _audit_payload(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "actor": row["actor"],
        "action": row["action"],
        "entity_type": row["entity_type"],
        "entity_id": row["entity_id"],
        "metadata": json.loads(row["metadata_json"] or "{}"),
        "created_at": row["created_at"],
    }


def _contact_payload(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "company_id": row["company_id"],
        "full_name": row["full_name"],
        "title": row["title"],
        "email": row["email"],
        "phone": row["phone"],
        "linkedin_url": row["linkedin_url"],
        "country": row["country"],
        "source": row["source"],
        "seniority": row["seniority"],
        "confidence": row["confidence"],
        "created_at": row["created_at"],
    }


def _suppression_payload(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "kind": row["kind"],
        "value": row["value"],
        "reason": row["reason"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
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


def _timeline_payload(logs: list[Any], drafts: list[Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for row in logs:
        items.append(
            {
                "type": "audit",
                "at": row["created_at"],
                "title": row["action"],
                "actor": row["actor"],
                "metadata": json.loads(row["metadata_json"] or "{}"),
            }
        )
    for row in drafts:
        items.append(
            {
                "type": "email_draft",
                "at": row["created_at"],
                "title": f"Email draft {row['status']}",
                "actor": row["reviewed_by"],
                "metadata": {"draft_id": row["id"], "subject": row["subject"], "status": row["status"]},
            }
        )
    return sorted(items, key=lambda item: item["at"] or "", reverse=True)


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


def _bearer_token(headers: dict[str, str]) -> str | None:
    authorization = ""
    for key, value in headers.items():
        if key.lower() == "authorization":
            authorization = value
            break
    if not authorization.lower().startswith("bearer "):
        return None
    return authorization.split(" ", 1)[1].strip() or None


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _format_time(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _empty_string_to_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _path_int(path: str, prefix: str) -> int:
    return int(path.removeprefix(prefix).split("/", 1)[0])


def _one(values: dict[str, list[str]], key: str) -> str:
    return values.get(key, [""])[0]


def _int_query(values: dict[str, list[str]], key: str, default: int) -> int:
    try:
        return int(_one(values, key) or default)
    except ValueError:
        return default
