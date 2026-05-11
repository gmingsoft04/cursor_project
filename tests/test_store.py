import tempfile
import unittest
from pathlib import Path

from fastcharge_leads.models import CompanyLead, ContactLead
from fastcharge_leads.store import LeadStore


class StoreTest(unittest.TestCase):
    def test_upsert_company_and_export(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = str(Path(directory) / "leads.sqlite3")
            csv_path = str(Path(directory) / "export.csv")
            store = LeadStore(db_path)
            lead = CompanyLead(
                company_name="Acme Imports",
                domain="acme.example",
                contacts=[ContactLead(full_name="Jane Buyer", email="jane@acme.example")],
                score=90,
            )
            store.upsert_company(lead)
            rows = store.list_companies()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["contact_count"], 1)
            store.export_companies_csv(csv_path)
            store.close()
            self.assertTrue(Path(csv_path).exists())


if __name__ == "__main__":
    unittest.main()
