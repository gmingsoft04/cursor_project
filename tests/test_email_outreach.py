import tempfile
import unittest
from pathlib import Path

from fastcharge_leads.clients.ai import LocalTemplateEmailGenerator
from fastcharge_leads.email_outreach import OutreachWorkflow, format_draft_preview
from fastcharge_leads.models import CompanyLead, ContactLead
from fastcharge_leads.store import LeadStore


class FakeSender:
    def __init__(self):
        self.sent = []

    def send(self, *, to_email, subject, body):
        self.sent.append((to_email, subject, body))


class EmailOutreachTest(unittest.TestCase):
    def test_generate_preview_approve_and_send_draft(self):
        with tempfile.TemporaryDirectory() as directory:
            store = LeadStore(str(Path(directory) / "leads.sqlite3"))
            company_id = store.upsert_company(
                CompanyLead(
                    company_name="Acme Mobile Accessories",
                    domain="acme.example",
                    country="United States",
                    product_interest="GaN fast charger",
                    score=95,
                    signals=["USB-C fast charger distributor"],
                    contacts=[ContactLead(full_name="Jane Buyer", email="jane@acme.example", title="Purchasing Manager")],
                )
            )
            self.assertGreater(company_id, 0)

            workflow = OutreachWorkflow(store=store, generator=LocalTemplateEmailGenerator())
            result = workflow.generate_drafts(limit=5, min_score=80, language="English")
            self.assertEqual(result.created, 1)

            draft = store.get_email_draft(result.draft_ids[0])
            self.assertIn("Subject:", format_draft_preview(draft))
            self.assertEqual(draft["status"], "draft")

            dry_run = workflow.send_approved(sender=FakeSender(), limit=5, dry_run=False)
            self.assertEqual(dry_run.sent, 0)

            store.review_email_draft(result.draft_ids[0], approved=True, reviewer="qa")
            sender = FakeSender()
            send_result = workflow.send_approved(sender=sender, limit=5)
            self.assertEqual(send_result.sent, 1)
            self.assertEqual(sender.sent[0][0], "jane@acme.example")
            self.assertEqual(store.get_email_draft(result.draft_ids[0])["status"], "sent")
            store.close()


if __name__ == "__main__":
    unittest.main()
