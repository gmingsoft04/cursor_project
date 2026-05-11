"""Lightweight web dashboard for lead review and outreach approval."""

from __future__ import annotations

import html
import json
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable
from urllib.parse import parse_qs, quote, unquote, urlparse

from .clients.ai import LocalTemplateEmailGenerator, OpenAICompatibleEmailGenerator
from .clients.email_sender import SmtpConfig, SmtpEmailSender
from .clients.http import JsonHttpClient
from .config import Settings
from .email_outreach import OutreachWorkflow
from .store import LeadStore


@dataclass(frozen=True, slots=True)
class WebResponse:
    status: int
    body: str
    content_type: str = "text/html; charset=utf-8"
    headers: dict[str, str] | None = None


class WebDashboard:
    def __init__(self, *, db_path: str, settings: Settings) -> None:
        self.db_path = db_path
        self.settings = settings

    def dispatch(self, method: str, raw_path: str, body: bytes = b"") -> WebResponse:
        parsed = urlparse(raw_path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        form = parse_qs(body.decode("utf-8")) if body else {}
        try:
            if method == "GET":
                return self._get(path, query)
            if method == "POST":
                return self._post(path, form)
            return self._page("Method not allowed", "<p>Unsupported method.</p>", status=405)
        except Exception as exc:  # pragma: no cover - keeps the web UI from returning empty responses.
            return self._page("Server error", f"<p class='error'>{_e(str(exc))}</p>", status=500)

    def _get(self, path: str, query: dict[str, list[str]]) -> WebResponse:
        if path == "/":
            return self._dashboard(query)
        if path == "/leads":
            return self._leads(query)
        if path == "/emails":
            return self._emails(query)
        if path.startswith("/emails/"):
            draft_id = _path_int(path, "/emails/")
            return self._email_detail(draft_id, query)
        return self._page("Not found", "<p>Page not found.</p>", status=404)

    def _post(self, path: str, form: dict[str, list[str]]) -> WebResponse:
        if path == "/emails/generate":
            return self._generate_email_drafts(form)
        if path == "/emails/send-approved":
            return self._send_approved(form)
        if path.startswith("/emails/"):
            remainder = path.removeprefix("/emails/")
            draft_id_text, _, action = remainder.partition("/")
            draft_id = int(draft_id_text)
            if action == "edit":
                return self._edit_email(draft_id, form)
            if action == "approve":
                return self._review_email(draft_id, approved=True, form=form)
            if action == "reject":
                return self._review_email(draft_id, approved=False, form=form)
        return self._page("Not found", "<p>Action not found.</p>", status=404)

    def _dashboard(self, query: dict[str, list[str]]) -> WebResponse:
        with _store(self.db_path) as store:
            companies = store.list_companies(limit=5)
            draft_counts = _draft_counts(store)
        cards = "".join(
            _stat_card(label, value)
            for label, value in [
                ("Top leads", str(len(companies))),
                ("Draft", str(draft_counts.get("draft", 0))),
                ("Approved", str(draft_counts.get("approved", 0))),
                ("Sent", str(draft_counts.get("sent", 0))),
            ]
        )
        rows = "".join(
            f"<tr><td>{_e(row['company_name'])}</td><td>{_e(row['country'])}</td>"
            f"<td>{_e(row['product_interest'])}</td><td>{row['contact_count']}</td><td>{row['score']}</td></tr>"
            for row in companies
        )
        empty_row = '<tr><td colspan="5">No leads yet.</td></tr>'
        body = _flash(query) + (
            f"<section class='cards'>{cards}</section>"
            "<section class='panel'><h2>Top leads</h2>"
            "<table><thead><tr><th>Company</th><th>Country</th><th>Product</th><th>Contacts</th><th>Score</th></tr></thead>"
            f"<tbody>{rows or empty_row}</tbody></table></section>"
        )
        return self._page("Dashboard", body)

    def _leads(self, query: dict[str, list[str]]) -> WebResponse:
        limit = _int_query(query, "limit", 100)
        with _store(self.db_path) as store:
            rows = store.list_companies(limit=limit)
        table_rows = "".join(
            f"<tr><td>{_e(row['company_name'])}</td><td>{_link(row['website'] or row['domain'])}</td>"
            f"<td>{_e(row['country'])}</td><td>{_e(row['product_interest'])}</td>"
            f"<td>{row['customs_matches']}</td><td>{row['contact_count']}</td><td>{row['score']}</td></tr>"
            for row in rows
        )
        empty_row = '<tr><td colspan="7">No leads yet.</td></tr>'
        body = _flash(query) + (
            "<section class='panel'><h2>Lead companies</h2>"
            "<table><thead><tr><th>Company</th><th>Website</th><th>Country</th><th>Product</th>"
            "<th>Customs</th><th>Contacts</th><th>Score</th></tr></thead>"
            f"<tbody>{table_rows or empty_row}</tbody></table></section>"
        )
        return self._page("Leads", body)

    def _emails(self, query: dict[str, list[str]]) -> WebResponse:
        status = _one(query, "status") or None
        limit = _int_query(query, "limit", 50)
        with _store(self.db_path) as store:
            drafts = store.list_email_drafts(status=status, limit=limit)
            draft_counts = _draft_counts(store)
        filters = " ".join(
            f"<a class='pill' href='/emails?status={_u(key)}'>{_e(key)} ({draft_counts.get(key, 0)})</a>"
            for key in ["draft", "approved", "rejected", "sent", "failed"]
        )
        rows = "".join(
            f"<tr><td><a href='/emails/{row['id']}'>#{row['id']}</a></td><td>{_e(row['company_name'])}</td>"
            f"<td>{_e(row['recipient_email'])}</td><td>{_e(row['subject'])}</td>"
            f"<td><span class='status'>{_e(row['status'])}</span></td><td>{_e(row['created_at'])}</td></tr>"
            for row in drafts
        )
        empty_row = '<tr><td colspan="6">No email drafts yet.</td></tr>'
        body = _flash(query) + (
            "<section class='panel'><h2>Generate outreach drafts</h2>"
            "<form method='post' action='/emails/generate' class='inline-form'>"
            "<label>Limit <input name='limit' type='number' value='20' min='1' max='200'></label>"
            "<label>Min score <input name='min_score' type='number' value='70' min='0' max='100'></label>"
            "<label>Language <input name='language' value='English'></label>"
            "<button type='submit'>Generate drafts</button></form></section>"
            "<section class='panel'><h2>Email drafts</h2>"
            f"<div class='filters'><a class='pill' href='/emails'>all</a> {filters}</div>"
            "<form method='post' action='/emails/send-approved' class='inline-form'>"
            "<label>Limit <input name='limit' type='number' value='20' min='1' max='200'></label>"
            "<button name='dry_run' value='1' type='submit'>Dry-run approved</button>"
            "<button name='send' value='1' type='submit' class='danger'>Send approved</button></form>"
            "<table><thead><tr><th>ID</th><th>Company</th><th>To</th><th>Subject</th><th>Status</th><th>Created</th></tr></thead>"
            f"<tbody>{rows or empty_row}</tbody></table></section>"
        )
        return self._page("Email drafts", body)

    def _email_detail(self, draft_id: int, query: dict[str, list[str]]) -> WebResponse:
        with _store(self.db_path) as store:
            draft = store.get_email_draft(draft_id)
        if not draft:
            return self._page("Draft not found", "<p>Draft not found.</p>", status=404)
        body = _flash(query) + (
            "<section class='panel'>"
            f"<h2>Draft #{draft['id']} <span class='status'>{_e(draft['status'])}</span></h2>"
            f"<p><strong>Company:</strong> {_e(draft['company_name'])}</p>"
            f"<p><strong>To:</strong> {_e(draft['recipient_name'] or '')} &lt;{_e(draft['recipient_email'])}&gt;</p>"
            f"<form method='post' action='/emails/{draft_id}/edit'>"
            f"<label>Subject <input name='subject' value='{_attr(draft['subject'])}'></label>"
            f"<label>Body <textarea name='body' rows='16'>{_e(draft['body'])}</textarea></label>"
            "<button type='submit'>Save reviewed content</button></form>"
            "<div class='actions'>"
            f"<form method='post' action='/emails/{draft_id}/approve'><input name='reviewer' placeholder='Reviewer'>"
            "<button type='submit'>Approve</button></form>"
            f"<form method='post' action='/emails/{draft_id}/reject'><input name='reviewer' placeholder='Reviewer'>"
            "<button type='submit' class='danger'>Reject</button></form>"
            "</div></section>"
        )
        return self._page(f"Draft #{draft_id}", body)

    def _generate_email_drafts(self, form: dict[str, list[str]]) -> WebResponse:
        limit = _int_form(form, "limit", 20)
        min_score = _int_form(form, "min_score", 70)
        language = _form(form, "language") or "English"
        with _store(self.db_path) as store:
            result = OutreachWorkflow(store=store, generator=self._generator()).generate_drafts(
                limit=limit,
                min_score=min_score,
                language=language,
            )
        return _redirect(f"/emails?message={_u(f'Generated {result.created} draft(s).')}")

    def _edit_email(self, draft_id: int, form: dict[str, list[str]]) -> WebResponse:
        subject = _form(form, "subject")
        body = _form(form, "body")
        if not subject or not body:
            return _redirect(f"/emails/{draft_id}?message={_u('Subject and body are required.')}")
        with _store(self.db_path) as store:
            store.update_email_draft_content(draft_id, subject=subject, body=body)
        return _redirect(f"/emails/{draft_id}?message={_u('Draft saved. Status reset to draft.')}")

    def _review_email(self, draft_id: int, *, approved: bool, form: dict[str, list[str]]) -> WebResponse:
        reviewer = _form(form, "reviewer") or "web"
        with _store(self.db_path) as store:
            store.review_email_draft(draft_id, approved=approved, reviewer=reviewer)
        status = "approved" if approved else "rejected"
        return _redirect(f"/emails/{draft_id}?message={_u(f'Draft {status}.')}")

    def _send_approved(self, form: dict[str, list[str]]) -> WebResponse:
        limit = _int_form(form, "limit", 20)
        dry_run = "dry_run" in form
        with _store(self.db_path) as store:
            result = OutreachWorkflow(store=store, generator=LocalTemplateEmailGenerator()).send_approved(
                sender=self._sender(),
                limit=limit,
                dry_run=dry_run,
            )
        prefix = "Dry-run matched" if dry_run else "Sent"
        return _redirect(f"/emails?status=approved&message={_u(f'{prefix} {result.sent}; failed {result.failed}.')}")

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

    def _page(self, title: str, body: str, *, status: int = 200) -> WebResponse:
        return WebResponse(
            status=status,
            body=(
                "<!doctype html><html><head><meta charset='utf-8'>"
                "<meta name='viewport' content='width=device-width, initial-scale=1'>"
                f"<title>{_e(title)} - FastCharge Leads</title>{_styles()}</head>"
                "<body><header><h1>FastCharge Leads</h1><nav>"
                "<a href='/'>Dashboard</a><a href='/leads'>Leads</a><a href='/emails'>Email drafts</a>"
                "</nav></header><main>"
                f"<h1>{_e(title)}</h1>{body}"
                "</main></body></html>"
            ),
        )


def run_web_server(*, db_path: str, settings: Settings, host: str = "127.0.0.1", port: int = 8080) -> None:
    dashboard = WebDashboard(db_path=db_path, settings=settings)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - standard library handler API.
            _send(self, dashboard.dispatch("GET", self.path))

        def do_POST(self) -> None:  # noqa: N802 - standard library handler API.
            length = int(self.headers.get("Content-Length", "0"))
            _send(self, dashboard.dispatch("POST", self.path, self.rfile.read(length)))

        def log_message(self, format: str, *args) -> None:  # noqa: A002 - standard library signature.
            return

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"FastCharge Leads web dashboard running at http://{host}:{port}")
    server.serve_forever()


def _send(handler: BaseHTTPRequestHandler, response: WebResponse) -> None:
    handler.send_response(response.status)
    handler.send_header("Content-Type", response.content_type)
    for key, value in (response.headers or {}).items():
        handler.send_header(key, value)
    handler.end_headers()
    handler.wfile.write(response.body.encode("utf-8"))


def _redirect(location: str) -> WebResponse:
    return WebResponse(status=303, body="", headers={"Location": location})


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


def _path_int(path: str, prefix: str) -> int:
    return int(path.removeprefix(prefix).split("/", 1)[0])


def _one(values: dict[str, list[str]], key: str) -> str:
    return values.get(key, [""])[0]


def _form(values: dict[str, list[str]], key: str) -> str:
    return values.get(key, [""])[0].strip()


def _int_query(values: dict[str, list[str]], key: str, default: int) -> int:
    try:
        return int(_one(values, key) or default)
    except ValueError:
        return default


def _int_form(values: dict[str, list[str]], key: str, default: int) -> int:
    try:
        return int(_form(values, key) or default)
    except ValueError:
        return default


def _flash(query: dict[str, list[str]]) -> str:
    message = _one(query, "message")
    return f"<div class='flash'>{_e(unquote(message))}</div>" if message else ""


def _stat_card(label: str, value: str) -> str:
    return f"<div class='card'><span>{_e(label)}</span><strong>{_e(value)}</strong></div>"


def _link(value: str | None) -> str:
    if not value:
        return ""
    href = value if "://" in value else f"https://{value}"
    return f"<a href='{_attr(href)}' target='_blank' rel='noreferrer'>{_e(value)}</a>"


def _e(value: object) -> str:
    return html.escape("" if value is None else str(value))


def _attr(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _u(value: str) -> str:
    return quote(value)


def _styles() -> str:
    return """
<style>
body{margin:0;background:#f7f8fb;color:#172033;font-family:Arial,Helvetica,sans-serif}
header{background:#111827;color:#fff;padding:18px 28px;display:flex;align-items:center;justify-content:space-between}
header h1{font-size:20px;margin:0}nav a{color:#fff;margin-left:18px;text-decoration:none}
main{padding:28px;max-width:1180px;margin:0 auto}.panel{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:20px;margin-bottom:20px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin-bottom:20px}.card{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:18px}.card span{color:#6b7280}.card strong{display:block;font-size:28px;margin-top:6px}
table{width:100%;border-collapse:collapse}th,td{border-bottom:1px solid #edf0f3;text-align:left;padding:10px;vertical-align:top}th{color:#4b5563;font-size:13px}
input,textarea{width:100%;box-sizing:border-box;border:1px solid #d1d5db;border-radius:8px;padding:9px;margin:5px 0 12px}textarea{font-family:Arial,Helvetica,sans-serif}
button{background:#2563eb;color:#fff;border:0;border-radius:8px;padding:10px 14px;cursor:pointer}.danger{background:#dc2626}
.inline-form{display:flex;gap:12px;align-items:end;flex-wrap:wrap}.inline-form label{min-width:130px}.inline-form input{margin-bottom:0}.actions{display:flex;gap:12px;margin-top:16px}.actions form{display:flex;gap:8px;align-items:center}.actions input{margin:0}
.pill{display:inline-block;background:#eef2ff;border-radius:999px;padding:6px 10px;margin:0 6px 10px 0;text-decoration:none;color:#3730a3}.status{font-weight:700}.flash{background:#ecfdf5;border:1px solid #a7f3d0;border-radius:8px;padding:12px;margin-bottom:16px}.error{color:#b91c1c}
</style>
"""
