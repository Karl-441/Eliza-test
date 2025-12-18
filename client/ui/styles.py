from PyQt5.QtGui import QColor, QFont, QPalette

class GFTheme:
    DARK_MODE = True
    BACKGROUND_COLOR = "#141414"
    BACKGROUND_SECONDARY = "#1F1F1F"
    BACKGROUND_TERTIARY = "#252525"
    ACCENT_COLOR = "#FFB400"
    ACCENT_HOVER = "#FFD700"
    ACCENT_DIM = "rgba(255, 180, 0, 0.3)"
    ACCENT_WARN = "#FF5500"
    ACCENT_DANGER = "#FF0000"
    TEXT_COLOR = "#E0E0E0"
    SECONDARY_TEXT = "#909090"
    DISABLED_TEXT = "#505050"
    INVERSE_TEXT = "#000000"
    SUCCESS_COLOR = "#00FF99"
    WARNING_COLOR = "#FF5500"
    ERROR_COLOR = "#FF0000"
    INFO_COLOR = "#00CCFF"
    DEBUG_COLOR = "#BD00FF"
    BORDER_COLOR = "#404040"
    GRID_COLOR = "rgba(255, 255, 255, 0.05)"
    FONT_FAMILY = '"Segoe UI", "Roboto", "Orbitron", sans-serif'
    FONT_MONO = '"JetBrains Mono", "Consolas", monospace'
    FONT_SIZE_H1 = 18
    FONT_SIZE_HEADER = 16
    FONT_SIZE_MAIN = 14
    FONT_SIZE_SMALL = 12
    SPACING_XS = 4
    SPACING_SM = 8
    SPACING_MD = 16
    SPACING_LG = 24
    SPACING_XL = 32
    TOUCH_TARGET_SIZE = 48
    HEADER_HEIGHT = 60
    INDICATOR_SIZE = 12
    ANIMATION_SPEED = 1.0
    
    @classmethod
    def toggle(cls):
        cls.DARK_MODE = not cls.DARK_MODE
        if cls.DARK_MODE:
            cls.BACKGROUND_COLOR = "#141414"
            cls.BACKGROUND_SECONDARY = "#1F1F1F"
            cls.BACKGROUND_TERTIARY = "#252525"
            cls.TEXT_COLOR = "#E0E0E0"
            cls.SECONDARY_TEXT = "#909090"
        else:
            cls.BACKGROUND_COLOR = "#F0F0F0"
            cls.BACKGROUND_SECONDARY = "#E5E5E5"
            cls.BACKGROUND_TERTIARY = "#DCDCDC"
            cls.TEXT_COLOR = "#141414"
            cls.SECONDARY_TEXT = "#505050"

    @classmethod
    def set_base_font_size(cls, base_px: int):
        base = max(12, min(24, int(base_px)))
        cls.FONT_SIZE_MAIN = base
        cls.FONT_SIZE_SMALL = max(12, int(base * 0.85))
        cls.FONT_SIZE_HEADER = max(14, int(base * 1.3))
        cls.FONT_SIZE_H1 = max(18, int(base * 1.7))

    @classmethod
    def set_animation_speed(cls, speed: float):
        cls.ANIMATION_SPEED = max(0.5, min(2.0, float(speed)))

    @classmethod
    def adjust_depth(cls, factor: float):
        factor = max(0.8, min(1.2, factor))
        def _scale_hex(hex_color):
            h = hex_color.lstrip("#")
            if len(h) != 6:
                return hex_color
            r = int(h[0:2], 16)
            g = int(h[2:4], 16)
            b = int(h[4:6], 16)
            r = max(0, min(255, int(r * factor)))
            g = max(0, min(255, int(g * factor)))
            b = max(0, min(255, int(b * factor)))
            return f"#{r:02X}{g:02X}{b:02X}"
        cls.BACKGROUND_COLOR = _scale_hex(cls.BACKGROUND_COLOR)
        cls.BACKGROUND_SECONDARY = _scale_hex(cls.BACKGROUND_SECONDARY)
        cls.BACKGROUND_TERTIARY = _scale_hex(cls.BACKGROUND_TERTIARY)
        cls.ACCENT_COLOR = _scale_hex(cls.ACCENT_COLOR)
        cls.ACCENT_HOVER = _scale_hex(cls.ACCENT_HOVER)
        cls.SECONDARY_TEXT = _scale_hex(cls.SECONDARY_TEXT)
        cls.BORDER_COLOR = _scale_hex(cls.BORDER_COLOR)

    @staticmethod
    def hex_to_rgba(hex_color, alpha=1.0):
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"rgba({r}, {g}, {b}, {alpha})"
        return hex_color
    @staticmethod
    def get_main_font():
        font = QFont("Segoe UI")
        font.setStyleHint(QFont.SansSerif)
        if not font.exactMatch():
            font = QFont("Roboto")
        font.setPointSize(GFTheme.FONT_SIZE_MAIN)
        return font
    @staticmethod
    def get_qss():
        return f"""
        QMainWindow, QDialog {{
            background-color: {GFTheme.BACKGROUND_COLOR};
            color: {GFTheme.TEXT_COLOR};
            font-family: {GFTheme.FONT_FAMILY};
        }}
        QWidget {{
            color: {GFTheme.TEXT_COLOR};
            font-family: {GFTheme.FONT_FAMILY};
        }}
        QTextEdit, QLineEdit {{
            background-color: {GFTheme.BACKGROUND_TERTIARY};
            border: 1px solid {GFTheme.BORDER_COLOR};
            color: {GFTheme.TEXT_COLOR};
            padding: {GFTheme.SPACING_SM}px;
            border-radius: 4px;
            selection-background-color: {GFTheme.ACCENT_DIM};
        }}
        QTextEdit:focus, QLineEdit:focus {{
            border: 1px solid {GFTheme.ACCENT_COLOR};
            background-color: {GFTheme.hex_to_rgba(GFTheme.ACCENT_COLOR, 0.05)};
        }}
        QListWidget {{
            background-color: {GFTheme.BACKGROUND_TERTIARY};
            border: 1px solid {GFTheme.BORDER_COLOR};
            border-radius: 4px;
            outline: none;
        }}
        QListWidget::item {{
            padding: {GFTheme.SPACING_SM}px;
            border-bottom: 1px solid {GFTheme.hex_to_rgba(GFTheme.BORDER_COLOR, 0.5)};
        }}
        QListWidget::item:selected {{
            background-color: {GFTheme.hex_to_rgba(GFTheme.ACCENT_COLOR, 0.1)};
            border-left: 3px solid {GFTheme.ACCENT_COLOR};
        }}
        QScrollBar:vertical {{
            border: none;
            background: {GFTheme.BACKGROUND_SECONDARY};
            width: 8px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {GFTheme.BORDER_COLOR};
            min-height: 20px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {GFTheme.ACCENT_COLOR};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QTabWidget::pane {{
            border: 1px solid {GFTheme.BORDER_COLOR};
            background: {GFTheme.BACKGROUND_COLOR};
        }}
        QTabBar::tab {{
            background: {GFTheme.BACKGROUND_SECONDARY};
            color: {GFTheme.SECONDARY_TEXT};
            padding: 8px 16px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{
            background: {GFTheme.BACKGROUND_TERTIARY};
            color: {GFTheme.ACCENT_COLOR};
            border-bottom: 2px solid {GFTheme.ACCENT_COLOR};
        }}
        QTabBar::tab:hover {{
            color: {GFTheme.TEXT_COLOR};
            background: {GFTheme.hex_to_rgba(GFTheme.ACCENT_COLOR, 0.1)};
        }}
        QToolTip {{
            background-color: {GFTheme.BACKGROUND_TERTIARY};
            color: {GFTheme.ACCENT_COLOR};
            border: 1px solid {GFTheme.ACCENT_COLOR};
            padding: 4px;
            opacity: 230;
        }}
        """
