
import unittest
import sys
import os
from PyQt5.QtWidgets import QApplication

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from client.ui.settings_dialog import SettingsDialog
from client.api_client import APIClient

app = QApplication(sys.argv)

class TestSettingsDialog(unittest.TestCase):
    def test_init(self):
        try:
            client = APIClient()
            dialog = SettingsDialog(None, client)
            self.assertIsNotNone(dialog)
            print("SettingsDialog initialized successfully")
        except Exception as e:
            self.fail(f"SettingsDialog initialization failed: {e}")

if __name__ == '__main__':
    unittest.main()
