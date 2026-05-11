"""Lead generation orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field

from .clients.apollo import ApolloClient
from .clients.customs import CustomsDataClient
from .clients.linkedin import LinkedInClient
from .clients.serper import SerperClient
from .models import CompanyLead, CustomsRecord, SearchResult
from .query_builder import BUYER_TITLES, SearchSeed, build_search_seeds
from .scoring import score_company
from .store import LeadStore
from .utils import extract_domain, extract_linkedin_company_url, infer_company_name, linkedin_vanity_from_url


@dataclass(slots=True)
class PipelineSummary:
    queries: int = 0
    web_results: int = 0
    customs_records: int = 0
    companies: int = 0
    contacts: int = 0
    dry_run_queries: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "queries": self.queries,
            "web_results": self.web_results,
            "customs_records": self.customs_records,
            "companies": self.companies,
            "contacts": self.contacts,
            "dry_run_queries": self.dry_run_queries,
        }


class LeadGenerationPipeline:
    def __init__(
        self,
        *,
        serper: SerperClient | None = None,
        apollo: ApolloClient | None = None,
        linkedin: LinkedInClient | None = None,
        customs: CustomsDataClient | None = None,
        store: LeadStore | None = None,
    ) -> None:
        self.serper = serper
        self.apollo = apollo
        self.linkedin = linkedin
        self.customs = customs
        self.store = store

    def run(
        self,
        *,
        products: list[str] | None = None,
        markets: list[str] | None = None,
        per_query: int = 10,
        max_queries: int | None = 20,
        dry_run: bool = False,
        persist: bool = True,
    ) -> PipelineSummary:
        products = products or []
        markets = markets or []
        seeds = build_search_seeds(products=products or None, markets=markets or None, max_queries=max_queries)
        summary = PipelineSummary(queries=len(seeds))
        if dry_run:
            summary.dry_run_queries = [seed.query for seed in seeds]
            return summary
        if not self.serper and not self.customs:
            raise ValueError("Configure SERPER_API_KEY and/or CUSTOMS_API_BASE to run lead generation.")

        leads: dict[str, CompanyLead] = {}
        if self.serper:
            for seed in seeds:
                results = self.serper.search(seed.query, limit=per_query)
                summary.web_results += len(results)
                for result in results:
                    lead = self._lead_from_search_result(result, seed)
                    self._merge_lead(leads, lead)

        if self.customs:
            for product in products:
                for market in markets or [None]:
                    records = self.customs.search_importers(product=product, country=market, limit=per_query)
                    summary.customs_records += len(records)
                    for record in records:
                        lead = self._lead_from_customs_record(record, product)
                        self._merge_lead(leads, lead)

        for lead in leads.values():
            self._enrich_linkedin(lead)
            self._enrich_contacts(lead)
            lead.score = score_company(lead)
            summary.contacts += len(lead.contacts)
            if persist and self.store:
                self.store.upsert_company(lead)
        summary.companies = len(leads)
        return summary

    def _lead_from_search_result(self, result: SearchResult, seed: SearchSeed) -> CompanyLead:
        domain = extract_domain(result.url)
        linkedin_url = extract_linkedin_company_url(result.url)
        signals = [seed.segment, result.snippet]
        return CompanyLead(
            company_name=infer_company_name(result.title, result.url),
            website=None if linkedin_url else result.url,
            domain=domain if domain and "linkedin.com" not in domain else None,
            country=seed.market,
            source=result.source,
            product_interest=seed.product,
            linkedin_url=linkedin_url,
            signals=[signal for signal in signals if signal],
            metadata={"search": result.metadata, "query": seed.query},
        )

    def _lead_from_customs_record(self, record: CustomsRecord, product: str) -> CompanyLead:
        return CompanyLead(
            company_name=record.importer_name,
            country=record.country,
            source=record.source,
            product_interest=product or record.product_description,
            customs_matches=1,
            signals=[signal for signal in [record.product_description, record.hs_code or ""] if signal],
            metadata={"customs": record.metadata, "exporter_name": record.exporter_name, "shipment_date": record.shipment_date},
        )

    def _merge_lead(self, leads: dict[str, CompanyLead], incoming: CompanyLead) -> None:
        key = incoming.fingerprint
        existing = leads.get(key)
        if not existing:
            leads[key] = incoming
            return
        existing.website = existing.website or incoming.website
        existing.domain = existing.domain or incoming.domain
        existing.country = existing.country or incoming.country
        existing.linkedin_url = existing.linkedin_url or incoming.linkedin_url
        existing.product_interest = existing.product_interest or incoming.product_interest
        existing.customs_matches += incoming.customs_matches
        existing.signals = _dedupe(existing.signals + incoming.signals)
        existing.metadata.update(incoming.metadata)

    def _enrich_linkedin(self, lead: CompanyLead) -> None:
        if not self.linkedin or not lead.linkedin_url:
            return
        vanity = linkedin_vanity_from_url(lead.linkedin_url)
        if not vanity:
            return
        organization = self.linkedin.organization_by_vanity(vanity)
        if not organization:
            return
        lead.metadata["linkedin"] = organization
        localized_name = organization.get("localizedName")
        if localized_name:
            lead.company_name = str(localized_name)

    def _enrich_contacts(self, lead: CompanyLead) -> None:
        if not self.apollo:
            return
        domains = [lead.domain] if lead.domain else None
        keywords = " ".join(part for part in [lead.company_name, lead.product_interest] if part)
        contacts = self.apollo.people_search(
            organization_domains=domains,
            keywords=keywords,
            titles=BUYER_TITLES,
            country=lead.country,
            per_page=5,
        )
        lead.contacts = contacts


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        normalized = value.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            output.append(value.strip())
    return output
