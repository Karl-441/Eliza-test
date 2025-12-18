from PyQt5.QtWidgets import QPushButton, QWidget, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QRectF, QByteArray
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath
from PyQt5.QtSvg import QSvgRenderer
from ..framework.theme import THEME

class TacticalButton(QPushButton):
    def __init__(self, text, parent=None, accent_color=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(48)
        self.setMinimumWidth(48)
        self.hovered = False
        self.accent_color = accent_color or THEME.get_color("accent")
        
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(10)
        self.shadow.setColor(QColor(self.accent_color))
        self.shadow.setEnabled(False)
        self.setGraphicsEffect(self.shadow)
        
        self._bg_alpha = 20
        self.anim = QPropertyAnimation(self, b"bg_alpha")
        self.anim.setDuration(THEME.anim["duration_fast"])
        self.anim.setEasingCurve(QEasingCurve.OutQuad)
        
        self.toggled.connect(self.update_anim_target)

    @pyqtProperty(int)
    def bg_alpha(self):
        return self._bg_alpha

    @bg_alpha.setter
    def bg_alpha(self, val):
        self._bg_alpha = val
        self.update()
        
    def set_accent_color(self, color):
        self.accent_color = color
        self.shadow.setColor(QColor(color if color else THEME.get_color("accent")))
        self.update()

    def update_anim_target(self):
        target = 20
        if self.isChecked():
            target = 150
            if self.hovered: target = 180
        elif self.hovered:
            target = 80
            
        self.anim.stop()
        self.anim.setEndValue(target)
        self.anim.start()
        
        if self.isEnabled() and (self.hovered or self.isChecked()):
            self.shadow.setEnabled(True)
        else:
            self.shadow.setEnabled(False)

    def enterEvent(self, event):
        self.hovered = True
        self.update_anim_target()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.hovered = False
        self.update_anim_target()
        super().leaveEvent(event)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        
        # Determine Color
        color_hex = self.accent_color or THEME.get_color("accent")
        base_color = QColor(color_hex)
        
        # Background
        bg_color = QColor(base_color)
        bg_color.setAlpha(self._bg_alpha)
        
        if not self.isEnabled():
            bg_color = QColor(THEME.get_color("text_secondary"))
            bg_color.setAlpha(20)
            
        path = QPainterPath()
        cut = 10
        path.moveTo(cut, 0)
        path.lineTo(rect.width(), 0)
        path.lineTo(rect.width(), rect.height() - cut)
        path.lineTo(rect.width() - cut, rect.height())
        path.lineTo(0, rect.height())
        path.lineTo(0, cut)
        path.closeSubpath()
        
        painter.fillPath(path, bg_color)
        
        pen = QPen(base_color)
        pen.setWidth(1)
        if not self.isEnabled():
            pen.setColor(QColor(THEME.get_color("text_secondary")))
        painter.setPen(pen)
        painter.drawPath(path)
        
        text_color = base_color
        if self.isChecked() or (self.hovered and self.isEnabled()):
            text_color = QColor(THEME.get_color("background"))
        elif not self.isEnabled():
            text_color = QColor(THEME.get_color("text_secondary"))
            
        painter.setPen(text_color)
        painter.setFont(THEME.get_font())
        painter.drawText(rect, Qt.AlignCenter, self.text())

class TacticalMapMarker(QWidget):
    def __init__(self, parent=None, size=32):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.renderer = QSvgRenderer()
        accent = THEME.get_color("accent")
        
        svg_content = f"""
        <svg width="{size}" height="{size}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <circle cx="50" cy="50" r="40" stroke="{accent}" stroke-width="4" fill="none"/>
            <circle cx="50" cy="50" r="20" stroke="{accent}" stroke-width="2" fill="{accent}" fill-opacity="0.3"/>
            <line x1="10" y1="50" x2="90" y2="50" stroke="{accent}" stroke-width="2"/>
            <line x1="50" y1="10" x2="50" y2="90" stroke="{accent}" stroke-width="2"/>
        </svg>
        """
        self.renderer.load(QByteArray(svg_content.encode('utf-8')))
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.renderer.render(painter, QRectF(self.rect()))
