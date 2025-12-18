import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from client.core.theme_manager import ThemeManager
from client.ui.styles import GFTheme

class TestThemeSync(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_client.base_url = "http://testserver"
        self.mock_client._get_headers.return_value = {}
        self.manager = ThemeManager(self.mock_client)
        
        # Save original colors
        self.orig_bg = GFTheme.BACKGROUND_COLOR

    def tearDown(self):
        GFTheme.BACKGROUND_COLOR = self.orig_bg

    @patch('requests.get')
    def test_fetch_theme(self, mock_get):
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "colors": {
                "background_primary": "#TESTBG",
                "accent_primary": "#TESTACCENT"
            },
            "fonts": {
                "family_main": "TestFont"
            }
        }
        mock_get.return_value = mock_response
        
        # Action
        result = self.manager.fetch_theme()
        
        # Assert
        self.assertTrue(result)
        self.assertEqual(GFTheme.BACKGROUND_COLOR, "#TESTBG")
        self.assertEqual(GFTheme.ACCENT_COLOR, "#TESTACCENT")
        self.assertEqual(GFTheme.FONT_FAMILY, "TestFont")

    @patch('requests.get')
    def test_check_updates(self, mock_get):
        # Mock Checksum response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"checksum": "new_hash"}
        mock_get.return_value = mock_response
        
        # Mock fetch_theme to avoid second call logic complexity
        self.manager.fetch_theme = MagicMock()
        
        # Action
        self.manager.check_updates()
        
        # Assert
        self.manager.fetch_theme.assert_called_once()
        self.assertEqual(self.manager.current_checksum, "new_hash")

if __name__ == '__main__':
    unittest.main()
