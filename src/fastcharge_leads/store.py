"""SQLite persistence and export helpers."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .models import CompanyLead, ContactLead, EmailDraft


class LeadStore:
    def __init__(self, path: str = "fastcharge_leads.sqlite3") -> None:
        self.path = path
        self._connection = sqlite3.connect(path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self.ensure_schema()

    def close(self) -> None:
        self._connection.close()

    def ensure_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint TEXT NOT NULL UNIQUE,
                company_name TEXT NOT NULL,
                website TEXT,
                domain TEXT,
                country TEXT,
                source TEXT,
                product_interest TEXT,
                linkedin_url TEXT,
                apollo_id TEXT,
                customs_matches INTEGER NOT NULL DEFAULT 0,
                signals_json TEXT NOT NULL DEFAULT '[]',
                score INTEGER NOT NULL DEFAULT 0,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                title TEXT,
                email TEXT,
                phone TEXT,
                linkedin_url TEXT,
                country TEXT,
                source TEXT,
                seniority TEXT,
                confidence REAL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(company_id, full_name, email, linkedin_url),
                FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS email_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                contact_id INTEGER,
                recipient_email TEXT NOT NULL,
                recipient_name TEXT,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'English',
                model TEXT,
                status TEXT NOT NULL DEFAULT 'draft',
                metadata_json TEXT NOT NULL DEFAULT '{}',
                reviewed_by TEXT,
                reviewed_at TEXT,
                sent_at TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
                FOREIGN KEY(contact_id) REFERENCES contacts(id) ON DELETE SET NULL
            );
            """
        )
        self._connection.commit()

    def upsert_company(self, lead: CompanyLead) -> int:
        payload = (
            lead.fingerprint,
            lead.company_name,
            lead.website,
            lead.domain,
            lead.country,
            lead.source,
            lead.product_interest,
            lead.linkedin_url,
            lead.apollo_id,
            lead.customs_matches,
            json.dumps(lead.signals, ensure_ascii=False),
            lead.score,
            json.dumps(lead.metadata, ensure_ascii=False, default=str),
        )
        self._connection.execute(
            """
            INSERT INTO companies (
                fingerprint, company_name, website, domain, country, source, product_interest,
                linkedin_url, apollo_id, customs_matches, signals_json, score, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fingerprint) DO UPDATE SET
                company_name=excluded.company_name,
                website=COALESCE(excluded.website, companies.website),
                domain=COALESCE(excluded.domain, companies.domain),
                country=COALESCE(excluded.country, companies.country),
                source=excluded.source,
                product_interest=COALESCE(excluded.product_interest, companies.product_interest),
                linkedin_url=COALESCE(excluded.linkedin_url, companies.linkedin_url),
                apollo_id=COALESCE(excluded.apollo_id, companies.apollo_id),
                customs_matches=MAX(excluded.customs_matches, companies.customs_matches),
                signals_json=excluded.signals_json,
                score=MAX(excluded.score, companies.score),
                metadata_json=excluded.metadata_json,
                updated_at=CURRENT_TIMESTAMP
            """,
            payload,
        )
        self._connection.commit()
        row = self._connection.execute("SELECT id FROM companies WHERE fingerprint = ?", (lead.fingerprint,)).fetchone()
        company_id = int(row["id"])
        self.add_contacts(company_id, lead.contacts)
        return company_id

    def add_contacts(self, company_id: int, contacts: Iterable[ContactLead]) -> None:
        for contact in contacts:
            self._connection.execute(
                """
                INSERT OR IGNORE INTO contacts (
                    company_id, full_name, title, email, phone, linkedin_url, country,
                    source, seniority, confidence, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    company_id,
                    contact.full_name,
                    contact.title,
                    contact.email,
                    contact.phone,
                    contact.linkedin_url,
                    contact.country,
                    contact.source,
                    contact.seniority,
                    contact.confidence,
                    json.dumps(contact.metadata, ensure_ascii=False, default=str),
                ),
            )
        self._connection.commit()

    def list_companies(self, limit: int = 100) -> list[sqlite3.Row]:
        return list(
            self._connection.execute(
                """
                SELECT c.*, COUNT(ct.id) AS contact_count
                FROM companies c
                LEFT JOIN contacts ct ON ct.company_id = c.id
                GROUP BY c.id
                ORDER BY c.score DESC, c.updated_at DESC
                LIMIT ?
                """,
                (limit,),
            )
        )

    def get_company(self, company_id: int) -> sqlite3.Row | None:
        return self._connection.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()

    def list_contacts_for_company(self, company_id: int) -> list[sqlite3.Row]:
        return list(
            self._connection.execute(
                """
                SELECT *
                FROM contacts
                WHERE company_id = ?
                ORDER BY CASE WHEN email IS NULL OR email = '' THEN 1 ELSE 0 END, created_at DESC
                """,
                (company_id,),
            )
        )

    def list_outreach_targets(self, *, limit: int = 20, min_score: int = 0) -> list[sqlite3.Row]:
        return list(
            self._connection.execute(
                """
                SELECT
                    c.id AS company_id,
                    c.company_name,
                    c.domain,
                    c.website,
                    c.country,
                    c.product_interest,
                    c.signals_json,
                    c.score,
                    ct.id AS contact_id,
                    ct.full_name AS recipient_name,
                    ct.email AS recipient_email,
                    ct.title AS recipient_title
                FROM companies c
                JOIN contacts ct ON ct.company_id = c.id
                WHERE ct.email IS NOT NULL
                  AND ct.email != ''
                  AND c.score >= ?
                ORDER BY c.score DESC, c.updated_at DESC, ct.created_at DESC
                LIMIT ?
                """,
                (min_score, limit),
            )
        )

    def create_email_draft(self, draft: EmailDraft) -> int:
        cursor = self._connection.execute(
            """
            INSERT INTO email_drafts (
                company_id, contact_id, recipient_email, recipient_name, subject, body,
                language, model, status, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                draft.company_id,
                draft.contact_id,
                draft.recipient_email,
                draft.recipient_name,
                draft.subject,
                draft.body,
                draft.language,
                draft.model,
                draft.status,
                json.dumps(draft.metadata, ensure_ascii=False, default=str),
            ),
        )
        self._connection.commit()
        return int(cursor.lastrowid)

    def get_email_draft(self, draft_id: int) -> sqlite3.Row | None:
        return self._connection.execute(
            """
            SELECT d.*, c.company_name
            FROM email_drafts d
            JOIN companies c ON c.id = d.company_id
            WHERE d.id = ?
            """,
            (draft_id,),
        ).fetchone()

    def list_email_drafts(self, *, status: str | None = None, limit: int = 50) -> list[sqlite3.Row]:
        if status:
            return list(
                self._connection.execute(
                    """
                    SELECT d.*, c.company_name
                    FROM email_drafts d
                    JOIN companies c ON c.id = d.company_id
                    WHERE d.status = ?
                    ORDER BY d.created_at DESC
                    LIMIT ?
                    """,
                    (status, limit),
                )
            )
        return list(
            self._connection.execute(
                """
                SELECT d.*, c.company_name
                FROM email_drafts d
                JOIN companies c ON c.id = d.company_id
                ORDER BY d.created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
        )

    def update_email_draft_content(self, draft_id: int, *, subject: str, body: str) -> None:
        self._connection.execute(
            """
            UPDATE email_drafts
            SET subject = ?, body = ?, status = 'draft', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (subject, body, draft_id),
        )
        self._connection.commit()

    def review_email_draft(self, draft_id: int, *, approved: bool, reviewer: str | None = None) -> None:
        status = "approved" if approved else "rejected"
        self._connection.execute(
            """
            UPDATE email_drafts
            SET status = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, reviewer, draft_id),
        )
        self._connection.commit()

    def mark_email_draft_sent(self, draft_id: int) -> None:
        self._connection.execute(
            """
            UPDATE email_drafts
            SET status = 'sent', sent_at = CURRENT_TIMESTAMP, error_message = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (draft_id,),
        )
        self._connection.commit()

    def mark_email_draft_failed(self, draft_id: int, error_message: str) -> None:
        self._connection.execute(
            """
            UPDATE email_drafts
            SET status = 'failed', error_message = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (error_message[:1000], draft_id),
        )
        self._connection.commit()

    def export_companies_csv(self, output_path: str, limit: int = 1000) -> None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        rows = self.list_companies(limit=limit)
        with open(output_path, "w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                "company_name",
                "domain",
                "website",
                "country",
                "product_interest",
                "linkedin_url",
                "customs_matches",
                "contact_count",
                "score",
                "signals",
            ])
            for row in rows:
                writer.writerow([
                    row["company_name"],
                    row["domain"],
                    row["website"],
                    row["country"],
                    row["product_interest"],
                    row["linkedin_url"],
                    row["customs_matches"],
                    row["contact_count"],
                    row["score"],
                    "; ".join(json.loads(row["signals_json"] or "[]")),
                ])
