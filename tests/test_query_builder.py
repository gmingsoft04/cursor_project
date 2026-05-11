import unittest

from fastcharge_leads.query_builder import build_search_seeds, normalize_csv_option


class QueryBuilderTest(unittest.TestCase):
    def test_build_search_seeds_limits_and_contains_context(self):
        seeds = build_search_seeds(products=["GaN fast charger"], markets=["United States"], max_queries=3)
        self.assertEqual(len(seeds), 3)
        self.assertTrue(all("GaN fast charger" in seed.query for seed in seeds))
        self.assertTrue(all(seed.market == "United States" for seed in seeds))

    def test_normalize_csv_option_dedupes(self):
        self.assertEqual(normalize_csv_option("US, Germany,US", []), ["US", "Germany"])


if __name__ == "__main__":
    unittest.main()
