"""命令行入口：搜索 → 抓取 → 评分 → 导出 CSV。"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
import time
from pathlib import Path

import yaml

from lead_finder.scraper import Lead, extract_leads
from lead_finder.search import search_queries

DEFAULT_REGIONS = (
    "us-en", "uk-en", "de-de", "fr-fr", "it-it",
    "es-es", "nl-nl", "se-sv", "ca-en", "au-en",
)


def _load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def run(
    *,
    config_path: Path,
    output_csv: Path,
    target_leads: int = 100,
    max_results_per_query: int = 25,
    pause_seconds: float = 2.0,
    respect_robots: bool = True,
    regions: tuple[str, ...] = DEFAULT_REGIONS,
) -> int:
    cfg = _load_config(config_path)
    queries = cfg.get("search_queries") or []
    preferred_prefixes = cfg.get("preferred_prefixes") or []
    blocklist_domains = set(cfg.get("blocklist_domains") or [])
    blocklist_locals = set(cfg.get("blocklist_locals") or [])

    if not queries:
        log = logging.getLogger(__name__)
        log.error("config 中没有 search_queries，无法继续。")
        return 2

    all_leads: dict[str, Lead] = {}

    for hit in search_queries(
        queries,
        max_results_per_query=max_results_per_query,
        regions=regions,
        pause_seconds=pause_seconds,
    ):
        leads = extract_leads(
            url=hit.url,
            company_hint=hit.title,
            snippet=hit.snippet,
            preferred_prefixes=preferred_prefixes,
            blocklist_domains=blocklist_domains,
            blocklist_locals=blocklist_locals,
            respect_robots=respect_robots,
        )
        for lead in leads:
            existing = all_leads.get(lead.email)
            if existing is None or lead.score > existing.score:
                all_leads[lead.email] = lead

        # 每抓一个站点也写一次中间结果，方便长跑断点
        _write_csv(output_csv, list(all_leads.values()))
        logging.info("Collected %d unique leads so far (target=%d)", len(all_leads), target_leads)
        if len(all_leads) >= target_leads * 2:
            # 留出余量，方便后续按分数挑选 top N
            break
        time.sleep(0.5)

    final = sorted(all_leads.values(), key=lambda l: l.score, reverse=True)[: target_leads]
    _write_csv(output_csv, final)
    logging.info("Done. %d leads exported to %s", len(final), output_csv)
    return 0


def _write_csv(path: Path, leads: list[Lead]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["company", "domain", "email", "country_hint", "score", "source_url", "snippet"])
        for l in leads:
            w.writerow([l.company, l.domain, l.email, l.country_hint, l.score, l.source_url, l.snippet])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Lead finder for fast-charger / USB-C cable B2B buyers (EU/US). "
            "仅抓取公开企业网站上发布的业务邮箱（info@/sales@/purchasing@ 等）。"
        )
    )
    parser.add_argument("--config", type=Path, default=Path("config/queries.yaml"))
    parser.add_argument("--output", type=Path, default=Path("output/leads.csv"))
    parser.add_argument("--target", type=int, default=100, help="目标 Lead 数量（默认 100）")
    parser.add_argument("--per-query", type=int, default=25, help="每条 query × region 抓取的搜索结果数")
    parser.add_argument("--pause", type=float, default=2.0, help="搜索间隔（秒），避免限流")
    parser.add_argument("--no-robots", action="store_true", help="不建议：忽略 robots.txt")
    parser.add_argument(
        "--regions",
        nargs="+",
        default=list(DEFAULT_REGIONS),
        help="DDG 区域代码，如 us-en uk-en de-de",
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    return run(
        config_path=args.config,
        output_csv=args.output,
        target_leads=args.target,
        max_results_per_query=args.per_query,
        pause_seconds=args.pause,
        respect_robots=not args.no_robots,
        regions=tuple(args.regions),
    )


if __name__ == "__main__":
    sys.exit(main())
