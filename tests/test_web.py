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

            app = WebApi(db_path=db_path, settings=Settings(auth_admin_username="admin", auth_admin_password="secret"))

            response = app.dispatch("GET", "/api/dashboard", headers=headers)
            self.assertEqual(response.status, 401)

            response = app.dispatch("POST", "/api/auth/login", b'{"username":"admin","password":"secret"}')
            self.assertEqual(response.status, 200)
            token = response.body["token"]
            headers = {"Authorization": f"Bearer {token}"}

            response = app.dispatch("GET", "/api/dashboard")
            self.assertEqual(response.status, 200)
            self.assertEqual(response.body["top_leads"][0]["company_name"], "Acme Mobile Accessories")

            response = app.dispatch("PUT", "/api/leads/1/crm", b'{"crm_status":"contacted","owner":"alice","crm_notes":"First call"}', headers=headers)
            self.assertEqual(response.status, 200)
            self.assertEqual(response.body["crm_status"], "contacted")

            response = app.dispatch("POST", "/api/email-drafts/generate", b'{"limit":1,"min_score":80,"language":"English"}', headers=headers)
            self.assertEqual(response.status, 201)
            self.assertEqual(response.body["created"], 1)

            response = app.dispatch("GET", "/api/email-drafts", headers=headers)
            self.assertIn("USB-C PD charger supply", response.body["items"][0]["subject"])

            response = app.dispatch("PUT", "/api/email-drafts/1", b'{"subject":"Reviewed subject","body":"Reviewed body"}', headers=headers)
            self.assertEqual(response.status, 200)
            self.assertEqual(response.body["subject"], "Reviewed subject")

            response = app.dispatch("GET", "/api/email-drafts/1", headers=headers)
            self.assertEqual(response.body["body"], "Reviewed body")

            response = app.dispatch("POST", "/api/email-drafts/1/approve", b'{"reviewer":"qa"}', headers=headers)
            self.assertEqual(response.status, 200)
            self.assertEqual(response.body["status"], "approved")

            response = app.dispatch("POST", "/api/email-drafts/send-approved", b'{"limit":1,"dry_run":true}', headers=headers)
            self.assertEqual(response.status, 200)
            self.assertEqual(response.body["sent"], 1)

            response = app.dispatch("GET", "/api/audit-logs", headers=headers)
            actions = [row["action"] for row in response.body["items"]]
            self.assertIn("companies.crm_update", actions)
            self.assertIn("email_drafts.approve", actions)


if __name__ == "__main__":
    unittest.main()
