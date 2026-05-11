"""Command line interface for FastCharge Leads."""

from __future__ import annotations

import argparse
import json
import sys

from .clients.apollo import ApolloClient
from .clients.customs import CustomsDataClient
from .clients.http import JsonHttpClient
from .clients.linkedin import LinkedInClient
from .clients.serper import SerperClient
from .config import Settings
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

    if args.command == "run":
        products = normalize_csv_option(args.products, DEFAULT_PRODUCTS)
        markets = normalize_csv_option(args.markets, DEFAULT_MARKETS)
        store = None if args.no_persist else LeadStore(db_path)
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


if __name__ == "__main__":
    sys.exit(main())
