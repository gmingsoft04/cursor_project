import os
import unittest

from fastcharge_leads.config import Settings


class SettingsTest(unittest.TestCase):
    def test_from_env_uses_defaults_with_slots_dataclass(self):
        previous = os.environ.pop("REQUEST_TIMEOUT_SECONDS", None)
        try:
            settings = Settings.from_env()
        finally:
            if previous is not None:
                os.environ["REQUEST_TIMEOUT_SECONDS"] = previous
        self.assertEqual(settings.apollo_api_base, "https://api.apollo.io/v1")
        self.assertEqual(settings.request_timeout_seconds, 20.0)


if __name__ == "__main__":
    unittest.main()
