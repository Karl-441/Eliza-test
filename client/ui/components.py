import random
import math
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QFrame, QOpenGLWidget, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty, QByteArray
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QLinearGradient, QRadialGradient, QPolygonF, QSurfaceFormat, QPixmap
from PyQt5.QtSvg import QSvgRenderer
from .styles import GFTheme

class TacticalMapMarker(QWidget):
    def __init__(self, parent=None, size=32):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.renderer = QSvgRenderer()
        
        # Embedded SVG for a tactical target marker
        svg_content = f"""
        <svg width="{size}" height="{size}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <circle cx="50" cy="50" r="40" stroke="{GFTheme.ACCENT_COLOR}" stroke-width="4" fill="none"/>
            <circle cx="50" cy="50" r="20" stroke="{GFTheme.ACCENT_COLOR}" stroke-width="2" fill="{GFTheme.ACCENT_COLOR}" fill-opacity="0.3"/>
            <line x1="10" y1="50" x2="90" y2="50" stroke="{GFTheme.ACCENT_COLOR}" stroke-width="2"/>
            <line x1="50" y1="10" x2="50" y2="90" stroke="{GFTheme.ACCENT_COLOR}" stroke-width="2"/>
            <path d="M 20 20 L 30 20 M 20 20 L 20 30" stroke="{GFTheme.ACCENT_COLOR}" stroke-width="4" fill="none"/>
            <path d="M 80 20 L 70 20 M 80 20 L 80 30" stroke="{GFTheme.ACCENT_COLOR}" stroke-width="4" fill="none"/>
            <path d="M 20 80 L 30 80 M 20 80 L 20 70" stroke="{GFTheme.ACCENT_COLOR}" stroke-width="4" fill="none"/>
            <path d="M 80 80 L 70 80 M 80 80 L 80 70" stroke="{GFTheme.ACCENT_COLOR}" stroke-width="4" fill="none"/>
        </svg>
        """
        self.renderer.load(QByteArray(svg_content.encode('utf-8')))
        
    def resizeEvent(self, event):
        # Responsive font size
        h = self.height()
        font_size = max(10, int(h * 0.35))
        font = GFTheme.get_main_font()
        font.setPointSize(font_size)
        font.setBold(True)
        self.setFont(font)
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.renderer.render(painter, QRectF(self.rect()))

class TacticalButton(QPushButton):
    def __init__(self, text, parent=None, accent_color=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(48) # Minimum 48px for touch targets
        self.setMinimumWidth(48) # Minimum 48px width
        self.hovered = False
        self.accent_color = accent_color or GFTheme.ACCENT_COLOR
        
        # Shadow Effect
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(10)
        self.shadow.setOffset(0, 0)
        self.shadow.setColor(QColor(self.accent_color))
        self.shadow.setEnabled(False) # Enable on hover/active
        self.setGraphicsEffect(self.shadow)
        
        # Animation
        self._bg_alpha = 20
        self.anim = QPropertyAnimation(self, b"bg_alpha")
        self.anim.setDuration(200)
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
        if self.shadow:
            self.shadow.setColor(QColor(color if color else GFTheme.ACCENT_COLOR))
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
        
        # Update shadow state
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
        color_hex = self.accent_color
        if not color_hex: color_hex = GFTheme.ACCENT_COLOR
        
        base_color = QColor(color_hex)
        
        # Background
        bg_color = QColor(base_color)
        
        # Logic for Alpha: Driven by animation
        alpha = self._bg_alpha
        bg_color.setAlpha(alpha)
            
        if not self.isEnabled():
            bg_color = QColor(GFTheme.SECONDARY_TEXT)
            bg_color.setAlpha(20)
            
        path = QPainterPath()
        # Cut corners design
        cut = 10
        path.moveTo(cut, 0)
        path.lineTo(rect.width(), 0)
        path.lineTo(rect.width(), rect.height() - cut)
        path.lineTo(rect.width() - cut, rect.height())
        path.lineTo(0, rect.height())
        path.lineTo(0, cut)
        path.closeSubpath()
        
        painter.fillPath(path, bg_color)
        
        # Border
        pen = QPen(base_color)
        pen.setWidth(1)
        if not self.isEnabled():
            pen.setColor(QColor(GFTheme.SECONDARY_TEXT))
            
        painter.setPen(pen)
        painter.drawPath(path)
        
        # Text
        text_color = QColor(base_color)
        if self.isChecked() or (self.hovered and self.isEnabled()):
            text_color = QColor(GFTheme.TEXT_COLOR) # White/Bright on active
        elif not self.isEnabled():
            text_color = QColor(GFTheme.SECONDARY_TEXT)
            
        painter.setPen(text_color)
        painter.setFont(GFTheme.get_main_font())
        painter.drawText(rect, Qt.AlignCenter, self.text())

class ParticleBackground(QOpenGLWidget):
    def __init__(self, parent=None, griffin_logo=None, sf_logo=None):
        super().__init__(parent)
        
        # Configure Surface Format for Antialiasing
        fmt = QSurfaceFormat()
        fmt.setSamples(4)
        self.setFormat(fmt)
        
        self.particles = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(16) # ~60 FPS
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_AlwaysStackOnTop, False) # Ensure it stays behind
        
        # Load Logos
        self.logo_griffin = QPixmap(griffin_logo) if griffin_logo else QPixmap()
        self.logo_sf = QPixmap(sf_logo) if sf_logo else QPixmap()
        
        # Initialize particles
        self.init_particles(600) # Target 500-800
        
        # Initialize Data Flows (Dashed trails)
        self.flows = []
        self.init_flows(15)
        
    def initializeGL(self):
        pass
        
    def resizeGL(self, w, h):
        pass
        
    def paintGL(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Draw Background
        bg = QColor(GFTheme.BACKGROUND_COLOR)
        painter.fillRect(self.rect(), bg)
        
        # Draw Logos (Tactical Integration)
        painter.setCompositionMode(QPainter.CompositionMode_Screen)
        
        if not self.logo_sf.isNull():
            sf_size = 500
            # Draw top-right
            sf_rect = QRectF(self.width() - sf_size + 100, -100, sf_size, sf_size)
            painter.setOpacity(0.15)
            painter.drawPixmap(sf_rect.toRect(), self.logo_sf)
            
        if not self.logo_griffin.isNull():
            griffin_size = 600
            # Draw bottom-left
            griffin_rect = QRectF(-150, self.height() - griffin_size + 150, griffin_size, griffin_size)
            painter.setOpacity(0.1)
            painter.drawPixmap(griffin_rect.toRect(), self.logo_griffin)
            
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setOpacity(1.0)
        
        # Draw Grid
        self.draw_grid(painter)
        
        # Draw Data Flows
        self.draw_flows(painter)
        
        # Draw Particles
        painter.setPen(Qt.NoPen)
        for p in self.particles:
            color = QColor(GFTheme.ACCENT_COLOR)
            color.setAlpha(p['alpha'])
            painter.setBrush(color)
            painter.drawEllipse(QPointF(p['x'], p['y']), p['size'], p['size'])

    def init_particles(self, count):
        for _ in range(count):
            self.particles.append(self.create_particle())
            
    def init_flows(self, count):
        for _ in range(count):
            self.flows.append(self.create_flow())

    def create_particle(self):
        return {
            'x': random.random() * self.width(),
            'y': random.random() * self.height(),
            'vx': (random.random() - 0.5) * 0.5,
            'vy': (random.random() - 0.5) * 0.5,
            'size': random.random() * 2 + 1,
            'alpha': random.randint(50, 150)
        }
        
    def create_flow(self):
        # Flows move along grid lines (multiples of 50)
        is_horz = random.choice([True, False])
        if is_horz:
            y = random.randint(0, 20) * 50
            return {
                'x': random.random() * self.width(),
                'y': y,
                'vx': random.random() * 2 + 2, # Faster than particles
                'vy': 0,
                'len': random.randint(50, 150),
                'horizontal': True
            }
        else:
            x = random.randint(0, 20) * 50
            return {
                'x': x,
                'y': random.random() * self.height(),
                'vx': 0,
                'vy': random.random() * 2 + 2,
                'len': random.randint(50, 150),
                'horizontal': False
            }
        
    def update_particles(self):
        w = self.width()
        h = self.height()
        if w == 0 or h == 0: return # Prevent issues during init
        
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            
            # Wrap around
            if p['x'] < 0: p['x'] = w
            if p['x'] > w: p['x'] = 0
            if p['y'] < 0: p['y'] = h
            if p['y'] > h: p['y'] = 0
            
        # Update flows
        for f in self.flows:
            f['x'] += f['vx']
            f['y'] += f['vy']
            
            if f['horizontal']:
                if f['x'] > w + f['len']: 
                    f['x'] = -f['len']
                    f['y'] = random.randint(0, h // 50) * 50 # Reset to a new random grid line
            else:
                if f['y'] > h + f['len']: 
                    f['y'] = -f['len']
                    f['x'] = random.randint(0, w // 50) * 50 # Reset to a new random grid line
            
        self.update() # Triggers paintGL
            
    def draw_grid(self, painter):
        # 15-20% opacity grid
        color = QColor(255, 255, 255, 40)
        pen = QPen(color)
        pen.setWidth(1)
        pen.setStyle(Qt.DotLine) # Dotted lines as requested
        painter.setPen(pen)
        
        grid_size = 50
        w = self.width()
        h = self.height()
        
        for x in range(0, w, grid_size):
            painter.drawLine(x, 0, x, h)
            
        for y in range(0, h, grid_size):
            painter.drawLine(0, y, w, y)

    def draw_flows(self, painter):
        pen = QPen(QColor(GFTheme.ACCENT_COLOR))
        pen.setWidth(2)
        pen.setStyle(Qt.DashLine)
        pen.setDashPattern([4, 4]) # 4px dash, 4px space
        color = QColor(GFTheme.ACCENT_COLOR)
        color.setAlpha(150) # Visible dashed lines
        pen.setColor(color)
        painter.setPen(pen)
        
        for f in self.flows:
            if f['horizontal']:
                painter.drawLine(int(f['x']), int(f['y']), int(f['x'] + f['len']), int(f['y']))
            else:
                painter.drawLine(int(f['x']), int(f['y']), int(f['x']), int(f['y'] + f['len']))

class RadarChart(QWidget):
    def __init__(self, data=None, labels=None, parent=None):
        super().__init__(parent)
        self.data = data or [0.8, 0.6, 0.9, 0.7, 0.5]
        self.labels = labels or ["LLM", "TTS", "ASR", "MEM", "NET"]
        self.setMinimumSize(200, 200)
        self.scan_angle = 0
        self._axis_scale = 0.0 # Animation value
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_scan)
        self.timer.start(50) # 20 FPS for scan
        
        # Axis Animation
        self.anim = QPropertyAnimation(self, b"axis_scale")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()
        
    @pyqtProperty(float)
    def axis_scale(self):
        return self._axis_scale

    @axis_scale.setter
    def axis_scale(self, value):
        self._axis_scale = value
        self.update()
        
    def update_scan(self):
        self.scan_angle = (self.scan_angle + 5) % 360
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        center = rect.center()
        radius = min(rect.width(), rect.height()) / 2 - 20
        
        # Draw web
        color = QColor(GFTheme.ACCENT_COLOR)
        color.setAlpha(100)
        pen = QPen(color)
        painter.setPen(pen)
        
        sides = len(self.data)
        angle_step = 2 * math.pi / sides
        
        # Concentric polygons
        anim_radius = radius * self._axis_scale
        
        for i in range(1, 5):
            r = anim_radius * i / 4
            points = []
            for j in range(sides):
                angle = j * angle_step - math.pi / 2
                x = center.x() + r * math.cos(angle)
                y = center.y() + r * math.sin(angle)
                points.append(QPointF(x, y))
            painter.drawPolygon(QPolygonF(points))
            
        # Spokes
        for j in range(sides):
            angle = j * angle_step - math.pi / 2
            x = center.x() + anim_radius * math.cos(angle)
            y = center.y() + anim_radius * math.sin(angle)
            painter.drawLine(center, QPointF(x, y))
            
            # Labels
            label_r = radius + 15
            lx = center.x() + label_r * math.cos(angle)
            ly = center.y() + label_r * math.sin(angle)
            painter.drawText(QRectF(lx-20, ly-10, 40, 20), Qt.AlignCenter, self.labels[j])
            
        # Data
        data_points = []
        for j, val in enumerate(self.data):
            angle = j * angle_step - math.pi / 2
            r = anim_radius * val
            x = center.x() + r * math.cos(angle)
            y = center.y() + r * math.sin(angle)
            data_points.append(QPointF(x, y))
            
        # Fill data area
        brush_color = QColor(GFTheme.ACCENT_COLOR)
        brush_color.setAlpha(100)
        painter.setBrush(brush_color)
        painter.setPen(QPen(QColor(GFTheme.ACCENT_COLOR), 2))
        painter.drawPolygon(QPolygonF(data_points))

        # Scan Line
        scan_rad = math.radians(self.scan_angle)
        scan_x = center.x() + radius * math.cos(scan_rad)
        scan_y = center.y() + radius * math.sin(scan_rad)
        
        gradient = QLinearGradient(center, QPointF(scan_x, scan_y))
        gradient.setColorAt(0, QColor(0, 0, 0, 0))
        gradient.setColorAt(1, QColor(GFTheme.ACCENT_COLOR))
        
        painter.setPen(QPen(QBrush(gradient), 2))
        painter.drawLine(center, QPointF(scan_x, scan_y))

class TacticalFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.NoFrame)
        self.glow_alpha = 100
        self.glow_dir = 5
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.pulse_glow)
        self.timer.start(100)
        
        # Shadow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setOffset(0, 0)
        self.shadow.setColor(QColor(0, 0, 0, 150))
        self.setGraphicsEffect(self.shadow)
        
    def pulse_glow(self):
        self.glow_alpha += self.glow_dir
        if self.glow_alpha >= 200 or self.glow_alpha <= 50:
            self.glow_dir *= -1
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        
        # Background
        painter.fillRect(rect, QColor(0, 0, 0, 100))
        
        # Corner brackets
        pen = QPen(QColor(GFTheme.ACCENT_COLOR))
        pen.setWidth(2)
        
        # Glow effect on brackets
        glow_color = QColor(GFTheme.ACCENT_COLOR)
        glow_color.setAlpha(self.glow_alpha)
        
        # Draw glow
        painter.setPen(QPen(glow_color, 4))
        l = 15 # bracket length
        
        # Top Left
        painter.drawLine(0, 0, l, 0)
        painter.drawLine(0, 0, 0, l)
        
        # Top Right
        painter.drawLine(rect.width(), 0, rect.width()-l, 0)
        painter.drawLine(rect.width(), 0, rect.width(), l)
        
        # Bottom Left
        painter.drawLine(0, rect.height(), l, rect.height())
        painter.drawLine(0, rect.height(), 0, rect.height()-l)
        
        # Bottom Right
        painter.drawLine(rect.width(), rect.height(), rect.width()-l, rect.height())
        painter.drawLine(rect.width(), rect.height(), rect.width(), rect.height()-l)
        
        # Draw sharp lines on top
        painter.setPen(pen)
        painter.drawLine(0, 0, l, 0)
        painter.drawLine(0, 0, 0, l)
        painter.drawLine(rect.width(), 0, rect.width()-l, 0)
        painter.drawLine(rect.width(), 0, rect.width(), l)
        painter.drawLine(0, rect.height(), l, rect.height())
        painter.drawLine(0, rect.height(), 0, rect.height()-l)
        painter.drawLine(rect.width(), rect.height(), rect.width()-l, rect.height())
        painter.drawLine(rect.width(), rect.height(), rect.width(), rect.height()-l)

