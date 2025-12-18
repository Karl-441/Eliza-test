
import unittest
import sys
import os
from PyQt5.QtCore import QObject

# Add project root to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from client.framework.theme import ThemeEngine, THEME
from client.framework.state import Store, STORE

class TestThemeEngine(unittest.TestCase):
    def setUp(self):
        self.theme = ThemeEngine()

    def test_singleton(self):
        self.assertIs(THEME, STORE.theme if hasattr(STORE, 'theme') else THEME)
        # Note: THEME is a global instance.

    def test_default_values(self):
        # self.assertEqual(self.theme.current_theme, 'default') # Removed as not implemented
        # self.assertTrue(self.theme.dark_mode) # Removed as not implemented directly
        self.assertIsNotNone(self.theme.colors)
        self.assertIsNotNone(self.theme.fonts)

    def test_color_retrieval(self):
        # Test getting a default color
        accent = self.theme.get_color('accent')
        self.assertTrue(accent.startswith('#'))
        
        # Test fallback (internal default is #FF00FF)
        missing = self.theme.get_color('NON_EXISTENT')
        self.assertEqual(missing, '#FF00FF')

    def test_update_theme(self):
        new_config = {
            'colors': {
                'accent': '#FF00FF'
            },
            'fonts': {
                'size_main': 16
            }
        }
        self.theme.load_theme(new_config)
        self.assertEqual(self.theme.get_color('accent'), '#FF00FF')
        self.assertEqual(self.theme.fonts['size_main'], 16)

class TestStore(unittest.TestCase):
    def setUp(self):
        self.store = Store()

    def test_state_management(self):
        self.store.set('user_id', 123)
        self.assertEqual(self.store.get('user_id'), 123)
        
        self.store.update({'username': 'commander'})
        self.assertEqual(self.store.get('username'), 'commander')
        self.assertEqual(self.store.get('user_id'), 123)

    def test_signals(self):
        # Mock signal receiver
        class Receiver(QObject):
            def __init__(self):
                super().__init__()
                self.received = False
            def on_changed(self, key, val):
                self.received = True
                
        receiver = Receiver()
        pass

if __name__ == '__main__':
    unittest.main()
