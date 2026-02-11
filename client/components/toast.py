from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QColor, QPainter, QBrush, QPen
from ..framework.theme import THEME
from ..framework.i18n import I18N

class TacticalToast(QWidget):
    """
    Non-intrusive notification overlay that fades in and out.
    """
    def __init__(self, parent, text, type="info", duration=3000):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.type = type
        self.duration = duration
        
        # Colors based on type
        self.color = THEME.get_color("accent")
        self.bg_color = THEME.get_color("background_secondary")
        if type == "success":
            self.color = THEME.get_color("success")
        elif type == "error":
            self.color = THEME.get_color("error")
        elif type == "warning":
            self.color = THEME.get_color("warning")
            
        # Layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(20, 10, 20, 10)
        
        # Icon/Symbol
        symbol_map = {
            "info": I18N.t("toast_symbol_info"), 
            "success": I18N.t("toast_symbol_success"), 
            "error": I18N.t("toast_symbol_error"), 
            "warning": I18N.t("toast_symbol_warning")
        }
        self.lbl_icon = QLabel(symbol_map.get(type, I18N.t("toast_symbol_info")))
        self.lbl_icon.setStyleSheet(f"color: {self.color}; font-size: 18px; font-weight: bold;")
        self.layout.addWidget(self.lbl_icon)
        
        # Text
        self.lbl_text = QLabel(text)
        self.lbl_text.setStyleSheet(f"color: {THEME.get_color('text_primary')}; font-size: 14px; font-family: {THEME.fonts['family_main']};")
        self.layout.addWidget(self.lbl_text)
        
        self.adjustSize()
        
        # Positioning (Bottom Center of Parent)
        if parent:
            p_rect = parent.rect()
            self.move(
                p_rect.center().x() - self.width() // 2,
                p_rect.bottom() - self.height() - 50
            )
            
        # Animation
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(300)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()
        
        # Auto-close timer
        QTimer.singleShot(duration, self.fade_out)
        
        self.show()
        
    def fade_out(self):
        self.anim.setDirection(QPropertyAnimation.Backward)
        self.anim.finished.connect(self.close)
        self.anim.start()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        
        # Background
        bg = QColor(self.bg_color)
        bg.setAlpha(240)
        painter.setBrush(QBrush(bg))
        
        # Border
        painter.setPen(QPen(QColor(self.color), 1))
        
        painter.drawRoundedRect(rect.adjusted(1,1,-1,-1), 4, 4)
        
        # Left Accent Line
        painter.fillRect(2, 2, 4, rect.height()-4, QColor(self.color))

    @staticmethod
    def show_toast(parent, text, type="info", duration=3000):
        TacticalToast(parent, text, type, duration)
