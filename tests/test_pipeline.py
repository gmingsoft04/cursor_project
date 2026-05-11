import unittest

from fastcharge_leads.models import ContactLead, CustomsRecord, SearchResult
from fastcharge_leads.pipeline import LeadGenerationPipeline


class FakeSerper:
    def search(self, query, *, country_code=None, limit=10):
        return [SearchResult(title="Acme Chargers - Wholesale", url="https://acme.example", snippet="USB-C fast charger distributor")]


class FakeApollo:
    def people_search(self, **kwargs):
        return [ContactLead(full_name="Jane Buyer", email="jane@acme.example", title="Procurement Manager")]


class FakeCustoms:
    def search_importers(self, *, product, country=None, limit=20):
        return [CustomsRecord(importer_name="Acme Chargers", product_description=product, country=country)]


class PipelineTest(unittest.TestCase):
    def test_pipeline_collects_merges_and_scores(self):
        pipeline = LeadGenerationPipeline(serper=FakeSerper(), apollo=FakeApollo(), customs=FakeCustoms())
        summary = pipeline.run(products=["GaN fast charger"], markets=["United States"], max_queries=1, per_query=2, persist=False)
        self.assertEqual(summary.queries, 1)
        self.assertEqual(summary.web_results, 1)
        self.assertEqual(summary.customs_records, 1)
        self.assertGreaterEqual(summary.companies, 1)
        self.assertGreaterEqual(summary.contacts, 1)

    def test_dry_run_returns_queries(self):
        pipeline = LeadGenerationPipeline()
        summary = pipeline.run(products=["USB-C cable"], markets=["Germany"], max_queries=2, dry_run=True)
        self.assertEqual(len(summary.dry_run_queries), 2)


if __name__ == "__main__":
    unittest.main()
