import unittest

from fastcharge_leads.models import CompanyLead, ContactLead
from fastcharge_leads.scoring import score_company


class ScoringTest(unittest.TestCase):
    def test_score_rewards_relevant_buying_signals(self):
        lead = CompanyLead(
            company_name="Acme Mobile Accessories Distributor",
            website="https://example.com",
            domain="example.com",
            country="United States",
            product_interest="GaN fast charger",
            customs_matches=2,
            contacts=[ContactLead(full_name="Jane Buyer", email="jane@example.com", title="Purchasing Manager")],
            signals=["wholesale USB-C fast charger importer"],
        )
        self.assertGreaterEqual(score_company(lead), 80)


if __name__ == "__main__":
    unittest.main()
