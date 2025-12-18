import sys
from PyQt5.QtWidgets import QApplication
from client.ui.components import TacticalMapMarker, TacticalButton, ParticleBackground, RadarChart
from client.ui.styles import GFTheme
from client.ui.main_window import MainWindow

def test_ui_components():
    app = QApplication(sys.argv)
    
    # Test GFTheme
    print(f"Testing GFTheme: {GFTheme.ACCENT_COLOR}, {GFTheme.SUCCESS_COLOR}")
    
    # Test Components
    try:
        marker = TacticalMapMarker()
        print("TacticalMapMarker initialized")
        
        btn = TacticalButton("Test")
        print("TacticalButton initialized")
        
        bg = ParticleBackground()
        print("ParticleBackground initialized")
        
        chart = RadarChart()
        print("RadarChart initialized")
        
    except Exception as e:
        print(f"Component initialization failed: {e}")
        return False
        
    print("UI Components verified successfully.")
    return True

if __name__ == "__main__":
    if test_ui_components():
        sys.exit(0)
    else:
        sys.exit(1)
