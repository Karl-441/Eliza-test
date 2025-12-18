from PyQt5.QtWidgets import QOpenGLWidget, QWidget, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF, pyqtProperty, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QSurfaceFormat, QLinearGradient, QPolygonF
from ..framework.theme import THEME
import random
import math

class ParticleBackground(QOpenGLWidget):
    def __init__(self, parent=None, griffin_logo=None, sf_logo=None):
        super().__init__(parent)
        fmt = QSurfaceFormat()
        fmt.setSamples(4)
        self.setFormat(fmt)
        
        self.particles = []
        self.flows = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(16)
        
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_AlwaysStackOnTop, False)
        
        self.logo_griffin = QPixmap(griffin_logo) if griffin_logo else QPixmap()
        self.logo_sf = QPixmap(sf_logo) if sf_logo else QPixmap()
        
        self.init_particles(600)
        self.init_flows(15)

    def initializeGL(self):
        pass
    def resizeGL(self, w, h):
        pass

    def init_particles(self, count):
        for _ in range(count):
            self.particles.append({
                'x': random.random() * 1920,
                'y': random.random() * 1080,
                'vx': (random.random() - 0.5) * 0.5,
                'vy': (random.random() - 0.5) * 0.5,
                'size': random.random() * 2 + 1,
                'alpha': random.randint(50, 150)
            })

    def init_flows(self, count):
        for _ in range(count):
            self.flows.append(self.create_flow())

    def create_flow(self):
        is_horz = random.choice([True, False])
        if is_horz:
            return {
                'x': random.random() * 1920,
                'y': random.randint(0, 20) * 50,
                'vx': random.random() * 2 + 2,
                'vy': 0,
                'len': random.randint(50, 150),
                'horizontal': True
            }
        else:
            return {
                'x': random.randint(0, 30) * 50,
                'y': random.random() * 1080,
                'vx': 0,
                'vy': random.random() * 2 + 2,
                'len': random.randint(50, 150),
                'horizontal': False
            }

    def update_particles(self):
        w = self.width()
        h = self.height()
        if w == 0: return
        
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            if p['x'] < 0: p['x'] = w
            if p['x'] > w: p['x'] = 0
            if p['y'] < 0: p['y'] = h
            if p['y'] > h: p['y'] = 0
            
        for f in self.flows:
            f['x'] += f['vx']
            f['y'] += f['vy']
            if f['horizontal']:
                if f['x'] > w + f['len']:
                    f['x'] = -f['len']
                    f['y'] = random.randint(0, h // 50) * 50
            else:
                if f['y'] > h + f['len']:
                    f['y'] = -f['len']
                    f['x'] = random.randint(0, w // 50) * 50
        self.update()

    def paintGL(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.fillRect(self.rect(), QColor(THEME.get_color("background")))
        
        painter.setCompositionMode(QPainter.CompositionMode_Screen)
        
        # Solar System Simulation (Lightweight)
        # Replaces Griffin/SF Logo logic if desired, or overlays. 
        # Requirement: Transparency ~45% (alpha ~115)
        self.draw_solar_system(painter)
        
        # Previous Logo Logic (kept for legacy or if needed, but reducing opacity to blend)
        if not self.logo_sf.isNull():
            painter.setOpacity(0.05)
            painter.drawPixmap(self.width() - 400, -100, 500, 500, self.logo_sf)
        if not self.logo_griffin.isNull():
            painter.setOpacity(0.05)
            painter.drawPixmap(-150, self.height() - 450, 600, 600, self.logo_griffin)
            
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setOpacity(1.0)
        
        # Grid
        grid_color = QColor(THEME.get_color("grid"))
        pen = QPen(grid_color)
        pen.setStyle(Qt.DotLine)
        painter.setPen(pen)
        for x in range(0, self.width(), 50):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 50):
            painter.drawLine(0, y, self.width(), y)
            
        # Flows
        accent = QColor(THEME.get_color("accent"))
        pen = QPen(accent)
        pen.setWidth(2)
        pen.setStyle(Qt.DashLine)
        pen.setDashPattern([4, 4])
        accent.setAlpha(150)
        pen.setColor(accent)
        painter.setPen(pen)
        for f in self.flows:
            if f['horizontal']:
                painter.drawLine(int(f['x']), int(f['y']), int(f['x']+f['len']), int(f['y']))
            else:
                painter.drawLine(int(f['x']), int(f['y']), int(f['x']), int(f['y']+f['len']))
                
        # Particles
        painter.setPen(Qt.NoPen)
        for p in self.particles:
            c = QColor(THEME.get_color("accent"))
            c.setAlpha(p['alpha'])
            painter.setBrush(c)
            painter.drawEllipse(QPointF(p['x'], p['y']), p['size'], p['size'])

        # CRT/LED Interference Filter
        self.draw_crt_effect(painter)

    def draw_solar_system(self, painter):
        w = self.width()
        h = self.height()
        cx, cy = w / 2, h / 2
        
        # Use time for orbit
        import time
        t = time.time() * 0.5
        
        painter.setPen(Qt.NoPen)
        
        # Sun
        sun_color = QColor("#FFD700")
        sun_color.setAlpha(115) # ~45% opacity
        painter.setBrush(sun_color)
        painter.drawEllipse(QPointF(cx, cy), 40, 40)
        
        # Planets
        orbits = [
            {'r': 100, 'speed': 1.0, 'size': 5, 'color': '#A0A0A0'},
            {'r': 180, 'speed': 0.7, 'size': 8, 'color': '#00CCFF'},
            {'r': 280, 'speed': 0.5, 'size': 12, 'color': '#FF5500', 'has_ring': True},
            {'r': 400, 'speed': 0.3, 'size': 10, 'color': '#00FF99'},
        ]
        
        for orb in orbits:
            # Draw Orbit Path
            path_color = QColor(THEME.get_color("accent"))
            path_color.setAlpha(30)
            painter.setPen(QPen(path_color, 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), orb['r'], orb['r'])
            
            # Draw Planet
            angle = t * orb['speed']
            px = cx + math.cos(angle) * orb['r']
            py = cy + math.sin(angle) * orb['r']
            
            p_color = QColor(orb['color'])
            p_color.setAlpha(115) # ~45% opacity
            painter.setPen(Qt.NoPen)
            painter.setBrush(p_color)
            painter.drawEllipse(QPointF(px, py), orb['size'], orb['size'])
            
            # Ring (for gas giants)
            if orb.get('has_ring'):
                ring_color = QColor(orb['color'])
                ring_color.setAlpha(80)
                painter.setPen(QPen(ring_color, 2))
                painter.setBrush(Qt.NoBrush)
                # Draw a tilted ring (ellipse)
                painter.translate(px, py)
                painter.rotate(45)
                painter.drawEllipse(QPointF(0, 0), orb['size'] + 8, orb['size'] + 2)
                painter.rotate(-45)
                painter.translate(-px, -py)

    def draw_crt_effect(self, painter):
        # Scanlines
        scanline_color = QColor(0, 0, 0, 50)
        painter.setPen(QPen(scanline_color, 1))
        for y in range(0, self.height(), 2):
            painter.drawLine(0, y, self.width(), y)
            
        # Interference / Glitch (Random horizontal strip glitch)
        if random.random() > 0.95:
            glitch_h = random.randint(2, 10)
            glitch_y = random.randint(0, self.height() - glitch_h)
            glitch_color = QColor(THEME.get_color("accent"))
            glitch_color.setAlpha(50)
            painter.fillRect(0, glitch_y, self.width(), glitch_h, glitch_color)

        # Noise (Simulated with random rectangles)
        noise_color = QColor(255, 255, 255, 15)
        painter.setPen(Qt.NoPen)
        painter.setBrush(noise_color)
        for _ in range(20):
            nx = random.randint(0, self.width())
            ny = random.randint(0, self.height())
            nw = random.randint(2, 50)
            nh = 1
            painter.drawRect(nx, ny, nw, nh)


class RadarChart(QWidget):
    def __init__(self, data=None, labels=None, parent=None):
        super().__init__(parent)
        self.data = data or [0.8, 0.6, 0.9, 0.7, 0.5]
        self.labels = labels or ["LLM", "TTS", "ASR", "MEM", "NET"]
        self.setMinimumSize(200, 200)
        self.scan_angle = 0
        self._axis_scale = 0.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_scan)
        self.timer.start(50)
        
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
        
        accent = QColor(THEME.get_color("accent"))
        accent_dim = QColor(accent)
        accent_dim.setAlpha(100)
        
        pen = QPen(accent_dim)
        painter.setPen(pen)
        
        sides = len(self.data)
        angle_step = 2 * math.pi / sides
        anim_radius = radius * self._axis_scale
        
        for i in range(1, 5):
            r = anim_radius * i / 4
            points = []
            for j in range(sides):
                angle = j * angle_step - math.pi / 2
                points.append(QPointF(center.x() + r * math.cos(angle), center.y() + r * math.sin(angle)))
            painter.drawPolygon(QPolygonF(points))
            
        for j in range(sides):
            angle = j * angle_step - math.pi / 2
            p = QPointF(center.x() + anim_radius * math.cos(angle), center.y() + anim_radius * math.sin(angle))
            painter.drawLine(center, p)
            
            label_r = radius + 15
            lx = center.x() + label_r * math.cos(angle)
            ly = center.y() + label_r * math.sin(angle)
            painter.drawText(QRectF(lx-20, ly-10, 40, 20), Qt.AlignCenter, self.labels[j])
            
        data_points = []
        for j, val in enumerate(self.data):
            angle = j * angle_step - math.pi / 2
            r = anim_radius * val
            data_points.append(QPointF(center.x() + r * math.cos(angle), center.y() + r * math.sin(angle)))
            
        brush_color = QColor(accent)
        brush_color.setAlpha(100)
        painter.setBrush(brush_color)
        painter.setPen(QPen(accent, 2))
        painter.drawPolygon(QPolygonF(data_points))
        
        # Scan Line
        scan_rad = math.radians(self.scan_angle)
        scan_x = center.x() + radius * math.cos(scan_rad)
        scan_y = center.y() + radius * math.sin(scan_rad)
        gradient = QLinearGradient(center, QPointF(scan_x, scan_y))
        gradient.setColorAt(0, QColor(0,0,0,0))
        gradient.setColorAt(1, accent)
        painter.setPen(QPen(QBrush(gradient), 2))
        painter.drawLine(center, QPointF(scan_x, scan_y))

class BootOverlay(QWidget):
    finished = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {THEME.get_color('background')};")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel("INITIALIZING NEURAL LINK...")
        lbl.setStyleSheet(f"color: {THEME.get_color('accent')}; font-size: 24px; font-weight: bold; letter-spacing: 4px;")
        layout.addWidget(lbl)
        
        self.bar = QFrame()
        self.bar.setFixedSize(300, 4)
        self.bar.setStyleSheet(f"background-color: {THEME.get_color('accent_dim')};")
        self.prog = QFrame(self.bar)
        self.prog.setFixedHeight(4)
        self.prog.setStyleSheet(f"background-color: {THEME.get_color('accent')};")
        layout.addWidget(self.bar, 0, Qt.AlignCenter)
        
        self.anim = QPropertyAnimation(self.prog, b"geometry")
        self.anim.setDuration(2000)
        self.anim.setStartValue(QRect(0, 0, 0, 4))
        self.anim.setEndValue(QRect(0, 0, 300, 4))
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.start()
        
        QTimer.singleShot(2000, self.finished.emit)
