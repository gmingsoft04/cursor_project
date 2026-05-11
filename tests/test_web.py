import tempfile
import unittest
from pathlib import Path

from fastcharge_leads.config import Settings
from fastcharge_leads.models import CompanyLead, ContactLead
from fastcharge_leads.store import LeadStore
from fastcharge_leads.web import WebDashboard


class WebDashboardTest(unittest.TestCase):
    def test_dashboard_email_review_flow(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = str(Path(directory) / "leads.sqlite3")
            store = LeadStore(db_path)
            store.upsert_company(
                CompanyLead(
                    company_name="Acme Mobile Accessories",
                    domain="acme.example",
                    country="United States",
                    product_interest="USB-C PD charger",
                    score=91,
                    signals=["mobile accessories distributor"],
                    contacts=[ContactLead(full_name="Jane Buyer", email="jane@acme.example")],
                )
            )
            store.close()

            app = WebDashboard(db_path=db_path, settings=Settings())
            response = app.dispatch("GET", "/")
            self.assertEqual(response.status, 200)
            self.assertIn("Dashboard", response.body)
            self.assertIn("Acme Mobile Accessories", response.body)

            response = app.dispatch("POST", "/emails/generate", b"limit=1&min_score=80&language=English")
            self.assertEqual(response.status, 303)

            response = app.dispatch("GET", "/emails")
            self.assertIn("USB-C PD charger supply", response.body)

            response = app.dispatch("POST", "/emails/1/edit", b"subject=Reviewed+subject&body=Reviewed+body")
            self.assertEqual(response.status, 303)

            response = app.dispatch("GET", "/emails/1")
            self.assertIn("Reviewed subject", response.body)
            self.assertIn("Reviewed body", response.body)

            response = app.dispatch("POST", "/emails/1/approve", b"reviewer=qa")
            self.assertEqual(response.status, 303)

            response = app.dispatch("POST", "/emails/send-approved", b"limit=1&dry_run=1")
            self.assertEqual(response.status, 303)
            self.assertIn("Dry-run", response.headers["Location"])


if __name__ == "__main__":
    unittest.main()
