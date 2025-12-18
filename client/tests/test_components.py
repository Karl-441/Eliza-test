
import unittest
import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from client.components.atoms import TacticalButton, TacticalMapMarker
from client.components.molecules import TacticalFrame, StatusIndicator

# Global QApplication instance
app = QApplication(sys.argv)

class TestComponents(unittest.TestCase):
    def test_tactical_button(self):
        btn = TacticalButton("Test")
        self.assertEqual(btn.text(), "Test")
        # Test custom property
        self.assertEqual(btn.bg_alpha, 20)
        
        # Test None color (Fix verification)
        btn.set_accent_color(None)
        # Should not raise error and paintEvent should handle it
        btn.repaint() 

        
    def test_tactical_map_marker(self):
        marker = TacticalMapMarker(size=64)
        self.assertEqual(marker.width(), 64)
        self.assertEqual(marker.height(), 64)
        
    def test_tactical_frame(self):
        frame = TacticalFrame()
        self.assertIsInstance(frame, QWidget)
        
    def test_status_indicator(self):
        indicator = StatusIndicator("TEST")
        indicator.set_status('online')
        self.assertEqual(indicator.value_label.text(), 'ONLINE') # Check label text, not status attribute
        indicator.set_status('error')
        self.assertEqual(indicator.value_label.text(), 'ERROR')

if __name__ == '__main__':
    unittest.main()
