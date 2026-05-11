"""AI-assisted outreach email workflow with human review gates."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .clients.ai import OutreachEmailGenerator
from .clients.email_sender import SmtpEmailSender
from .models import EmailDraft
from .store import LeadStore


@dataclass(frozen=True, slots=True)
class DraftGenerationResult:
    created: int
    draft_ids: list[int]

    def as_dict(self) -> dict[str, object]:
        return {"created": self.created, "draft_ids": self.draft_ids}


@dataclass(frozen=True, slots=True)
class SendResult:
    sent: int
    failed: int
    draft_ids: list[int]

    def as_dict(self) -> dict[str, object]:
        return {"sent": self.sent, "failed": self.failed, "draft_ids": self.draft_ids}


class OutreachWorkflow:
    def __init__(self, *, store: LeadStore, generator: OutreachEmailGenerator) -> None:
        self.store = store
        self.generator = generator

    def generate_drafts(self, *, limit: int = 20, min_score: int = 0, language: str = "English") -> DraftGenerationResult:
        targets = self.store.list_outreach_targets(limit=limit, min_score=min_score)
        draft_ids: list[int] = []
        for target in targets:
            context = _context_from_target(target, language=language)
            generated = self.generator.generate(context)
            draft = EmailDraft(
                company_id=int(target["company_id"]),
                contact_id=int(target["contact_id"]) if target["contact_id"] is not None else None,
                recipient_email=str(target["recipient_email"]),
                recipient_name=target["recipient_name"],
                subject=generated.subject,
                body=generated.body,
                language=language,
                model=generated.model,
                metadata={"context": context, "raw_response": generated.raw_response},
            )
            draft_ids.append(self.store.create_email_draft(draft))
        return DraftGenerationResult(created=len(draft_ids), draft_ids=draft_ids)

    def send_approved(self, *, sender: SmtpEmailSender, limit: int = 20, dry_run: bool = False) -> SendResult:
        drafts = self.store.list_email_drafts(status="approved", limit=limit)
        sent = 0
        failed = 0
        processed_ids: list[int] = []
        for draft in drafts:
            draft_id = int(draft["id"])
            processed_ids.append(draft_id)
            if self.store.is_suppressed_email(str(draft["recipient_email"])):
                failed += 1
                if not dry_run:
                    self.store.mark_email_draft_failed(draft_id, "Recipient is on the suppression list.")
                continue
            if dry_run:
                sent += 1
                continue
            try:
                sender.send(to_email=draft["recipient_email"], subject=draft["subject"], body=draft["body"])
            except Exception as exc:  # pragma: no cover - exact SMTP errors depend on provider.
                failed += 1
                self.store.mark_email_draft_failed(draft_id, str(exc))
            else:
                sent += 1
                self.store.mark_email_draft_sent(draft_id)
        return SendResult(sent=sent, failed=failed, draft_ids=processed_ids)


def format_draft_preview(draft: Any) -> str:
    return (
        f"Draft #{draft['id']} [{draft['status']}]\n"
        f"Company: {draft['company_name']}\n"
        f"To: {draft['recipient_name'] or ''} <{draft['recipient_email']}>\n"
        f"Subject: {draft['subject']}\n\n"
        f"{draft['body']}\n"
    )


def _context_from_target(target: Any, *, language: str) -> dict[str, Any]:
    signals = json.loads(target["signals_json"] or "[]")
    return {
        "company_name": target["company_name"],
        "domain": target["domain"],
        "website": target["website"],
        "country": target["country"],
        "product_interest": target["product_interest"],
        "score": target["score"],
        "recipient_name": target["recipient_name"],
        "recipient_email": target["recipient_email"],
        "recipient_title": target["recipient_title"],
        "signals": signals[:5],
        "language": language,
    }
