import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from client.api_client import APIClient
from client.core.theme_manager import ThemeManager
from client.ui.styles import GFTheme

class TestClientAPI(unittest.TestCase):
    def test_headers(self):
        c = APIClient(api_key="k")
        self.assertEqual(c._get_headers()["X-API-Key"], "k")

    @patch("requests.get")
    def test_get_status_path(self, mget):
        mget.return_value = MagicMock(status_code=200, json=lambda: {"ok": True})
        c = APIClient()
        data = c.get_status()
        self.assertIn("ok", data)
        args, kwargs = mget.call_args
        self.assertTrue(args[0].endswith("/api/v1/system/status"))

class TestThemeManager(unittest.TestCase):
    @patch("requests.get")
    def test_fetch_theme_updates_styles(self, mget):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "dark_mode": True,
            "colors": {
                "background_primary": "#000001",
                "accent_primary": "#abcdef"
            },
            "fonts": {"family_main": "TestF"},
            "spacing": {"md": 18}
        }
        mget.return_value = resp
        client = APIClient()
        mgr = ThemeManager(client)
        ok = mgr.fetch_theme()
        self.assertTrue(ok)
        self.assertEqual(GFTheme.BACKGROUND_COLOR, "#000001")
        self.assertEqual(GFTheme.ACCENT_COLOR, "#abcdef")
        self.assertEqual(GFTheme.FONT_FAMILY, "TestF")
        self.assertEqual(GFTheme.SPACING_MD, 18)

if __name__ == "__main__":
    unittest.main()
