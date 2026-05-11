"""SQLite persistence and export helpers."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .models import CompanyLead, ContactLead


class LeadStore:
    def __init__(self, path: str = "fastcharge_leads.sqlite3") -> None:
        self.path = path
        self._connection = sqlite3.connect(path)
        self._connection.row_factory = sqlite3.Row
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
