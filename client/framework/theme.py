from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont

# THEME VERSION: 1.1.0
# Updated: Integrated ParticleBackground support for SettingsDialog
# Ensure visual consistency across all windows

class ThemeSignals(QObject):
    theme_changed = pyqtSignal()

class ThemeEngine(QObject):
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeEngine, cls).__new__(cls)
            cls._instance.signals = ThemeSignals()
            cls._instance._init_defaults()
        return cls._instance

    def _init_defaults(self):
        # Default "Tactical" Theme
        self.colors = {
            "background": "#0D1A2B",
            "background_secondary": "#152436",
            "background_tertiary": "#1D2E42",
            "accent": "#F0C419",
            "accent_hover": "#FFD700",
            "accent_dim": "rgba(240, 196, 25, 0.3)",
            "text_primary": "#E0E0E0",
            "text_secondary": "#A0A0A0",
            "border": "#F0C419",
            "success": "#00FF99",
            "warning": "#FF4444",
            "error": "#FF0000",
            "grid": "rgba(255, 255, 255, 0.15)"
        }
        
        self.fonts = {
            "family_main": '"Source Han Sans", "Microsoft YaHei", "Segoe UI", sans-serif',
            "family_code": '"Consolas", "JetBrains Mono", monospace',
            "size_h1": 24,
            "size_h2": 20,
            "size_h3": 18,
            "size_body": 14,
            "size_small": 12
        }
        
        self.spacing = {
            "xs": 4,
            "s": 8,
            "m": 16,
            "l": 24,
            "xl": 32
        }
        
        self.anim = {
            "duration_fast": 200,
            "duration_normal": 300,
            "easing": "OutQuad"
        }
        
        self.current_theme = "dark"
        self.themes = {
            "dark": self.colors.copy(),
            "light": {
                "background": "#F0F0F0",
                "background_secondary": "#FFFFFF",
                "background_tertiary": "#E0E0E0",
                "accent": "#007ACC",
                "accent_hover": "#0099FF",
                "accent_dim": "rgba(0, 122, 204, 0.3)",
                "text_primary": "#333333",
                "text_secondary": "#666666",
                "border": "#007ACC",
                "success": "#00CC66",
                "warning": "#FF3333",
                "error": "#FF0000",
                "grid": "rgba(0, 0, 0, 0.1)"
            }
        }

    def toggle(self):
        new_theme = "light" if self.current_theme == "dark" else "dark"
        self.current_theme = new_theme
        self.colors = self.themes[new_theme].copy()
        self.signals.theme_changed.emit()

    def set_base_font_size(self, size):
        if size <= 0: return
        # Scale all fonts based on ratio of new body size to default body size (14)
        ratio = size / 14.0
        defaults = {
            "size_h1": 24, "size_h2": 20, "size_h3": 18, 
            "size_body": 14, "size_small": 12
        }
        for k, v in defaults.items():
            self.fonts[k] = int(v * ratio)
        self.signals.theme_changed.emit()

    def get_color(self, key, alpha=1.0):
        c = self.colors.get(key, "#FF00FF")
        if alpha < 1.0:
            return self.hex_to_rgba(c, alpha)
        return c

    def get_font(self, type="body"):
        f = QFont(self.fonts["family_main"])
        if type == "code":
            f = QFont(self.fonts["family_code"])
        
        size = self.fonts.get(f"size_{type}", 14)
        f.setPixelSize(size)
        
        if type in ["h1", "h2", "h3"]:
            f.setBold(True)
            
        return f

    @staticmethod
    def hex_to_rgba(hex_color, alpha=1.0):
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"rgba({r}, {g}, {b}, {alpha})"
        return hex_color

    def load_theme(self, theme_data):
        """Load theme from dict (API/JSON)"""
        if "colors" in theme_data:
            self.colors.update(theme_data["colors"])
        if "fonts" in theme_data:
            self.fonts.update(theme_data["fonts"])
        self.signals.theme_changed.emit()

    def get_qss(self):
        return f"""
        QDialog, QMainWindow {{
            background-color: {self.get_color("background")};
            color: {self.get_color("text_primary")};
            font-family: "{self.fonts["family_main"]}";
        }}
        QWidget {{
            color: {self.get_color("text_primary")};
            font-family: "{self.fonts["family_main"]}";
        }}
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
            background-color: {self.get_color("background_tertiary")};
            border: 1px solid {self.get_color("border")};
            color: {self.get_color("text_primary")};
            padding: {self.spacing["s"]}px;
            border-radius: 4px;
            selection-background-color: {self.get_color("accent_dim")};
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border: 1px solid {self.get_color("accent")};
            background-color: {self.hex_to_rgba(self.get_color("accent"), 0.05)};
        }}
        QListWidget {{
            background-color: {self.get_color("background_secondary")};
            border: 1px solid {self.get_color("border")};
            border-radius: 4px;
            outline: none;
        }}
        QListWidget::item {{
            padding: {self.spacing["s"]}px;
            border-bottom: 1px solid {self.hex_to_rgba(self.get_color("border"), 0.5)};
        }}
        QListWidget::item:selected {{
            background-color: {self.hex_to_rgba(self.get_color("accent"), 0.1)};
            border-left: 3px solid {self.get_color("accent")};
            color: {self.get_color("accent")};
        }}
        QScrollBar:vertical {{
            border: none;
            background: {self.get_color("background")};
            width: 8px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {self.get_color("border")};
            min-height: 20px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {self.get_color("accent")};
        }}
        QTabWidget::pane {{
            border: 1px solid {self.get_color("border")};
            background: {self.get_color("background")};
        }}
        QTabBar::tab {{
            background: {self.get_color("background_secondary")};
            color: {self.get_color("text_secondary")};
            padding: 8px 16px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{
            background: {self.get_color("background_tertiary")};
            color: {self.get_color("accent")};
            border-bottom: 2px solid {self.get_color("accent")};
        }}
        QComboBox {{
            background-color: {self.get_color("background_tertiary")};
            border: 1px solid {self.get_color("border")};
            color: {self.get_color("text_primary")};
            padding: 4px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {self.get_color("background_secondary")};
            color: {self.get_color("text_primary")};
            selection-background-color: {self.get_color("accent")};
        }}
        """

THEME = ThemeEngine()
