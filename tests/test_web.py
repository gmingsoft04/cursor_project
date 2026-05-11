import tempfile
import unittest
from pathlib import Path

from fastcharge_leads.config import Settings
from fastcharge_leads.models import CompanyLead, ContactLead
from fastcharge_leads.store import LeadStore
from fastcharge_leads.web import WebApi


class WebApiTest(unittest.TestCase):
    def test_api_email_review_flow(self):
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

            app = WebApi(db_path=db_path, settings=Settings())
            response = app.dispatch("GET", "/api/dashboard")
            self.assertEqual(response.status, 200)
            self.assertEqual(response.body["top_leads"][0]["company_name"], "Acme Mobile Accessories")

            response = app.dispatch("POST", "/api/email-drafts/generate", b'{"limit":1,"min_score":80,"language":"English"}')
            self.assertEqual(response.status, 201)
            self.assertEqual(response.body["created"], 1)

            response = app.dispatch("GET", "/api/email-drafts")
            self.assertIn("USB-C PD charger supply", response.body["items"][0]["subject"])

            response = app.dispatch("PUT", "/api/email-drafts/1", b'{"subject":"Reviewed subject","body":"Reviewed body"}')
            self.assertEqual(response.status, 200)
            self.assertEqual(response.body["subject"], "Reviewed subject")

            response = app.dispatch("GET", "/api/email-drafts/1")
            self.assertEqual(response.body["body"], "Reviewed body")

            response = app.dispatch("POST", "/api/email-drafts/1/approve", b'{"reviewer":"qa"}')
            self.assertEqual(response.status, 200)
            self.assertEqual(response.body["status"], "approved")

            response = app.dispatch("POST", "/api/email-drafts/send-approved", b'{"limit":1,"dry_run":true}')
            self.assertEqual(response.status, 200)
            self.assertEqual(response.body["sent"], 1)


if __name__ == "__main__":
    unittest.main()
