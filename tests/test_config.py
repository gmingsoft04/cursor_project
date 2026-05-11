import os
import tempfile
import unittest
from pathlib import Path

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

    def test_from_env_loads_dotenv_without_overriding_exported_values(self):
        previous_cwd = os.getcwd()
        previous_key = os.environ.pop("SERPER_API_KEY", None)
        previous_timeout = os.environ.get("REQUEST_TIMEOUT_SECONDS")
        os.environ["REQUEST_TIMEOUT_SECONDS"] = "7"
        try:
            with tempfile.TemporaryDirectory() as directory:
                Path(directory, ".env").write_text("SERPER_API_KEY=from-file\nREQUEST_TIMEOUT_SECONDS=99\n", encoding="utf-8")
                os.chdir(directory)
                settings = Settings.from_env()
        finally:
            os.chdir(previous_cwd)
            if previous_key is None:
                os.environ.pop("SERPER_API_KEY", None)
            else:
                os.environ["SERPER_API_KEY"] = previous_key
            if previous_timeout is None:
                os.environ.pop("REQUEST_TIMEOUT_SECONDS", None)
            else:
                os.environ["REQUEST_TIMEOUT_SECONDS"] = previous_timeout
        self.assertEqual(settings.serper_api_key, "from-file")
        self.assertEqual(settings.request_timeout_seconds, 7.0)


if __name__ == "__main__":
    unittest.main()
