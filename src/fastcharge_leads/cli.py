"""Command line interface for FastCharge Leads."""

from __future__ import annotations

import argparse
import json
import sys

from .clients.ai import LocalTemplateEmailGenerator, OpenAICompatibleEmailGenerator
from .clients.apollo import ApolloClient
from .clients.customs import CustomsDataClient
from .clients.email_sender import SmtpConfig, SmtpEmailSender
from .clients.http import JsonHttpClient
from .clients.linkedin import LinkedInClient
from .clients.serper import SerperClient
from .config import Settings
from .email_outreach import OutreachWorkflow, format_draft_preview
from .pipeline import LeadGenerationPipeline
from .query_builder import DEFAULT_MARKETS, DEFAULT_PRODUCTS, normalize_csv_option
from .store import LeadStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Foreign trade lead generation for phone fast chargers and fast charging cables.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Collect and enrich company/customer leads.")
    run.add_argument("--products", help="Comma-separated product keywords.")
    run.add_argument("--markets", help="Comma-separated target markets/countries.")
    run.add_argument("--per-query", type=int, default=10, help="Results to request from each provider query.")
    run.add_argument("--max-queries", type=int, default=20, help="Maximum Serper search queries to run.")
    run.add_argument("--dry-run", action="store_true", help="Print generated search queries without calling APIs.")
    run.add_argument("--no-persist", action="store_true", help="Do not write results into SQLite.")
    run.add_argument("--db", help="SQLite database path. Defaults to LEADS_DB_PATH.")

    export = subparsers.add_parser("export", help="Export ranked company leads to CSV.")
    export.add_argument("--db", help="SQLite database path. Defaults to LEADS_DB_PATH.")
    export.add_argument("--output", default="exports/fastcharge_leads.csv", help="CSV output path.")
    export.add_argument("--limit", type=int, default=1000, help="Maximum companies to export.")

    schema = subparsers.add_parser("init-db", help="Create or upgrade the local SQLite schema.")
    schema.add_argument("--db", help="SQLite database path. Defaults to LEADS_DB_PATH.")

    generate = subparsers.add_parser("email-generate", help="Generate AI outreach email drafts for lead contacts.")
    generate.add_argument("--db", help="SQLite database path. Defaults to LEADS_DB_PATH.")
    generate.add_argument("--limit", type=int, default=20, help="Maximum email drafts to generate.")
    generate.add_argument("--min-score", type=int, default=0, help="Minimum company score to target.")
    generate.add_argument("--language", default="English", help="Email language, for example English or 中文.")

    preview = subparsers.add_parser("email-preview", help="Preview generated outreach email drafts.")
    preview.add_argument("--db", help="SQLite database path. Defaults to LEADS_DB_PATH.")
    preview.add_argument("--id", type=int, help="Preview one draft id.")
    preview.add_argument("--status", help="Filter drafts by status: draft, approved, rejected, sent, failed.")
    preview.add_argument("--limit", type=int, default=10, help="Maximum drafts to preview.")

    edit = subparsers.add_parser("email-edit", help="Replace a draft's subject/body after manual review.")
    edit.add_argument("--db", help="SQLite database path. Defaults to LEADS_DB_PATH.")
    edit.add_argument("--id", type=int, required=True, help="Draft id to edit.")
    edit.add_argument("--subject", required=True, help="Reviewed subject line.")
    edit.add_argument("--body-file", required=True, help="Path to a UTF-8 text file containing the reviewed body.")

    approve = subparsers.add_parser("email-approve", help="Approve a draft so it can be sent.")
    approve.add_argument("--db", help="SQLite database path. Defaults to LEADS_DB_PATH.")
    approve.add_argument("--id", type=int, required=True, help="Draft id to approve.")
    approve.add_argument("--reviewer", help="Reviewer name or identifier.")

    reject = subparsers.add_parser("email-reject", help="Reject a draft and prevent sending.")
    reject.add_argument("--db", help="SQLite database path. Defaults to LEADS_DB_PATH.")
    reject.add_argument("--id", type=int, required=True, help="Draft id to reject.")
    reject.add_argument("--reviewer", help="Reviewer name or identifier.")

    send = subparsers.add_parser("email-send", help="Send approved outreach emails via SMTP.")
    send.add_argument("--db", help="SQLite database path. Defaults to LEADS_DB_PATH.")
    send.add_argument("--limit", type=int, default=20, help="Maximum approved drafts to send.")
    send.add_argument("--dry-run", action="store_true", help="Show which approved drafts would be sent without using SMTP.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = Settings.from_env()
    db_path = args.db or settings.leads_db_path

    if args.command == "init-db":
        store = LeadStore(db_path)
        store.close()
        print(json.dumps({"database": db_path, "status": "ready"}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "export":
        store = LeadStore(db_path)
        store.export_companies_csv(args.output, limit=args.limit)
        store.close()
        print(json.dumps({"output": args.output, "status": "exported"}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "email-generate":
        store = LeadStore(db_path)
        http = JsonHttpClient(settings.request_timeout_seconds)
        generator = _build_email_generator(settings, http)
        try:
            result = OutreachWorkflow(store=store, generator=generator).generate_drafts(
                limit=args.limit,
                min_score=args.min_score,
                language=args.language,
            )
        finally:
            store.close()
        print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "email-preview":
        store = LeadStore(db_path)
        try:
            if args.id:
                draft = store.get_email_draft(args.id)
                if not draft:
                    print(json.dumps({"error": f"draft {args.id} not found"}, ensure_ascii=False, indent=2), file=sys.stderr)
                    return 1
                print(format_draft_preview(draft))
            else:
                for draft in store.list_email_drafts(status=args.status, limit=args.limit):
                    print(format_draft_preview(draft))
        finally:
            store.close()
        return 0

    if args.command == "email-edit":
        store = LeadStore(db_path)
        try:
            with open(args.body_file, encoding="utf-8") as file:
                body = file.read()
            store.update_email_draft_content(args.id, subject=args.subject, body=body)
        finally:
            store.close()
        print(json.dumps({"draft_id": args.id, "status": "draft", "updated": True}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "email-approve":
        store = LeadStore(db_path)
        try:
            store.review_email_draft(args.id, approved=True, reviewer=args.reviewer)
        finally:
            store.close()
        print(json.dumps({"draft_id": args.id, "status": "approved"}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "email-reject":
        store = LeadStore(db_path)
        try:
            store.review_email_draft(args.id, approved=False, reviewer=args.reviewer)
        finally:
            store.close()
        print(json.dumps({"draft_id": args.id, "status": "rejected"}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "email-send":
        store = LeadStore(db_path)
        sender = SmtpEmailSender(
            SmtpConfig(
                host=settings.smtp_host or "",
                port=settings.smtp_port,
                username=settings.smtp_username,
                password=settings.smtp_password,
                from_email=settings.smtp_from_email,
                from_name=settings.smtp_from_name,
                use_tls=settings.smtp_use_tls,
            )
        )
        try:
            result = OutreachWorkflow(store=store, generator=LocalTemplateEmailGenerator()).send_approved(
                sender=sender,
                limit=args.limit,
                dry_run=args.dry_run,
            )
        finally:
            store.close()
        print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "run":
        products = normalize_csv_option(args.products, DEFAULT_PRODUCTS)
        markets = normalize_csv_option(args.markets, DEFAULT_MARKETS)
        store = None if args.no_persist or args.dry_run else LeadStore(db_path)
        http = JsonHttpClient(settings.request_timeout_seconds)
        pipeline = LeadGenerationPipeline(
            serper=SerperClient(settings.serper_api_key, http=http) if settings.serper_api_key else None,
            apollo=ApolloClient(settings.apollo_api_key, settings.apollo_api_base, http=http) if settings.apollo_api_key else None,
            linkedin=LinkedInClient(settings.linkedin_access_token, settings.linkedin_api_base, http=http) if settings.linkedin_access_token else None,
            customs=CustomsDataClient(settings.customs_api_base, settings.customs_api_key, settings.customs_import_endpoint, http=http)
            if settings.customs_api_base
            else None,
            store=store,
        )
        try:
            summary = pipeline.run(
                products=products,
                markets=markets,
                per_query=args.per_query,
                max_queries=args.max_queries,
                dry_run=args.dry_run,
                persist=not args.no_persist,
            )
        finally:
            if store:
                store.close()
        print(json.dumps(summary.as_dict(), ensure_ascii=False, indent=2))
        return 0

    parser.print_help()
    return 2


def _build_email_generator(settings: Settings, http: JsonHttpClient):
    if settings.ai_api_key:
        return OpenAICompatibleEmailGenerator(
            api_key=settings.ai_api_key,
            api_base=settings.ai_api_base,
            model=settings.ai_model,
            http=http,
        )
    return LocalTemplateEmailGenerator()


if __name__ == "__main__":
    sys.exit(main())
