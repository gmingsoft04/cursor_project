"""Search query generation tailored to phone fast chargers and cables."""

from __future__ import annotations

from dataclasses import dataclass

from .utils import unique_preserve_order

DEFAULT_PRODUCTS = [
    "GaN fast charger",
    "USB-C PD charger",
    "phone fast charger",
    "fast charging cable",
    "USB-C fast charging cable",
    "iPhone fast charging cable",
]

DEFAULT_MARKETS = ["United States", "Germany", "United Kingdom", "Netherlands", "United Arab Emirates"]

BUYER_TITLES = [
    "owner",
    "founder",
    "ceo",
    "purchasing manager",
    "procurement manager",
    "sourcing manager",
    "category manager",
    "import manager",
    "buyer",
]

SEGMENTS = [
    "importer",
    "distributor",
    "wholesaler",
    "mobile accessories retailer",
    "electronics retailer",
    "ecommerce seller",
]


@dataclass(frozen=True, slots=True)
class SearchSeed:
    query: str
    product: str
    market: str
    segment: str


def build_search_seeds(
    products: list[str] | None = None,
    markets: list[str] | None = None,
    max_queries: int | None = None,
) -> list[SearchSeed]:
    products = products or DEFAULT_PRODUCTS
    markets = markets or DEFAULT_MARKETS
    seeds: list[SearchSeed] = []
    templates = [
        '"{product}" {segment} "{market}"',
        '"{product}" "{market}" "contact us"',
        '"{product}" "{market}" "wholesale"',
        'site:linkedin.com/company "{product}" "{market}"',
    ]
    for product in products:
        for market in markets:
            for segment in SEGMENTS:
                seeds.append(SearchSeed(templates[0].format(product=product, segment=segment, market=market), product, market, segment))
            for template in templates[1:]:
                seeds.append(SearchSeed(template.format(product=product, market=market), product, market, "web"))
    deduped: list[SearchSeed] = []
    seen = set()
    for seed in seeds:
        if seed.query not in seen:
            seen.add(seed.query)
            deduped.append(seed)
    if max_queries is not None:
        return deduped[:max_queries]
    return deduped


def normalize_csv_option(value: str | None, fallback: list[str]) -> list[str]:
    if not value:
        return fallback
    return unique_preserve_order([part.strip() for part in value.split(",") if part.strip()])
