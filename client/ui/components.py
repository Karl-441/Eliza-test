from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from .styles import GFTheme

class UniversalContextMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Styling
        style = f"""
            QMenu {{
                background-color: {GFTheme.BACKGROUND_SECONDARY};
                border: 1px solid {GFTheme.ACCENT_COLOR};
                color: {GFTheme.TEXT_COLOR};
                padding: 4px;
            }}
            QMenu::item {{
                padding: 12px 24px; /* Larger touch target ~48px height */
                background-color: transparent;
            }}
            QMenu::item:selected {{
                background-color: {GFTheme.ACCENT_DIM};
                color: {GFTheme.ACCENT_HOVER};
            }}
            QMenu::separator {{
                height: 1px;
                background: {GFTheme.BORDER_COLOR};
                margin: 4px 8px;
            }}
        """
        self.setStyleSheet(style)
        
    def add_tactical_action(self, text, callback, icon=None):
        action = QAction(text, self)
        if icon:
            action.setIcon(icon)
        action.triggered.connect(callback)
        # Accessibility support
        action.setStatusTip(text)
        action.setToolTip(text)
        self.addAction(action)
        return action
        
    def showEvent(self, event):
        # Fade-in animation
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(120)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)
        self.anim.start()
        super().showEvent(event)
