from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem, QGraphicsPathItem, QGraphicsTextItem, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter, QPainterPath, QFont
from ..framework.theme import THEME
from ..framework.i18n import I18N
from ..components import TacticalButton
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal

class DAGNode(QGraphicsItem):
    def __init__(self, task_id, label, status="pending", on_click=None):
        super().__init__()
        self.task_id = task_id
        self.label = label
        self.status = status
        self.on_click = on_click
        self.width = 180
        self.height = 70
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
    
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.on_click:
            self.on_click(self.task_id)
        
    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)
        
    def paint(self, painter, option, widget):
        # Determine color based on status
        color = THEME.get_color("background_secondary")
        border_color = THEME.get_color("border")
        
        if self.status == "completed":
            border_color = THEME.get_color("success")
            color = THEME.hex_to_rgba(THEME.get_color("success"), 0.1)
        elif self.status == "in_progress":
            border_color = THEME.get_color("accent")
            color = THEME.hex_to_rgba(THEME.get_color("accent"), 0.1)
        elif self.status == "error":
            border_color = THEME.get_color("error")
            color = THEME.hex_to_rgba(THEME.get_color("error"), 0.1)
        elif self.status == "pending":
            border_color = THEME.get_color("text_secondary")
            
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw Box
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width, self.height, 5, 5)
        painter.fillPath(path, QBrush(QColor(color)))
        
        pen = QPen(QColor(border_color))
        pen.setWidth(2)
        if self.isSelected():
            pen.setColor(QColor(THEME.get_color("text_primary")))
            pen.setStyle(Qt.DashLine)
            
        painter.setPen(pen)
        painter.drawPath(path)
        
        # Draw Text
        painter.setPen(QColor(THEME.get_color("text_primary")))
        font = QFont(THEME.fonts["family_main"], 10)
        painter.setFont(font)
        
        rect = QRectF(10, 5, self.width-20, self.height-10)
        painter.drawText(rect, Qt.AlignCenter | Qt.TextWordWrap, self.label)
        
        # Status Label
        painter.setPen(QColor(THEME.get_color("text_secondary")))
        font_small = QFont(THEME.fonts["family_code"], 8)
        painter.setFont(font_small)
        painter.drawText(QRectF(5, self.height-15, self.width-10, 15), Qt.AlignRight, self.status.upper())

class DAGEdge(QGraphicsPathItem):
    def __init__(self, start_node, end_node):
        super().__init__()
        self.start_node = start_node
        self.end_node = end_node
        self.setZValue(-1) # Behind nodes
        self.update_path()
        
    def update_path(self):
        start_pos = self.start_node.scenePos()
        end_pos = self.end_node.scenePos()
        
        # Anchor points
        start = QPointF(start_pos.x() + self.start_node.width/2, start_pos.y() + self.start_node.height)
        end = QPointF(end_pos.x() + self.end_node.width/2, end_pos.y())
        
        path = QPainterPath()
        path.moveTo(start)
        
        # Cubic Bezier
        ctrl1 = QPointF(start.x(), start.y() + 50)
        ctrl2 = QPointF(end.x(), end.y() - 50)
        path.cubicTo(ctrl1, ctrl2, end)
        
        self.setPath(path)
        self.setPen(QPen(QColor(THEME.get_color("grid")), 2))

from client.framework.i18n import I18N

class DAGVisualizer(QGraphicsView):
    node_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor(THEME.get_color("background_tertiary"))))
        self.nodes = {} # id -> DAGNode
        self.edges = []
        self.tasks_data = []
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        
    def update_graph(self, tasks):
        self.tasks_data = tasks
        self.scene.clear()
        self.nodes = {}
        self.edges = []
        
        if not tasks:
            return

        # Simple layout logic
        # Map id to task
        task_map = {t['id']: t for t in tasks}
        
        # Assign levels
        def get_level(tid, visited=None):
            if visited is None: visited = set()
            if tid in visited: return 0 # Cycle?
            visited.add(tid)
            
            t = task_map.get(tid)
            if not t: return 0
            deps = t.get('dependencies', [])
            if not deps: return 0
            
            return 1 + max([get_level(d, visited) for d in deps], default=-1)

        level_groups = {}
        for t in tasks:
            lvl = get_level(t['id'])
            if lvl not in level_groups: level_groups[lvl] = []
            level_groups[lvl].append(t)
            
        # Create Nodes
        y_spacing = 120
        x_spacing = 220
        
        start_x = 50
        start_y = 50
        
        # Center horizontally based on max width
        max_width = max([len(g) for g in level_groups.values()]) * x_spacing
        
        for lvl in sorted(level_groups.keys()):
            tasks_in_lvl = level_groups[lvl]
            row_width = len(tasks_in_lvl) * x_spacing
            current_x = start_x + (max_width - row_width) / 2
            
            for i, t in enumerate(tasks_in_lvl):
                node = DAGNode(t['id'], t.get('description', t['id']), t.get('status', 'pending'), 
                             on_click=lambda tid: self.node_clicked.emit(tid))
                x = current_x + i * x_spacing
                y = start_y + lvl * y_spacing
                node.setPos(x, y)
                self.scene.addItem(node)
                self.nodes[t['id']] = node
                
        # Create Edges
        for t in tasks:
            node = self.nodes.get(t['id'])
            for dep_id in t.get('dependencies', []):
                dep_node = self.nodes.get(dep_id)
                if node and dep_node:
                    edge = DAGEdge(dep_node, node)
                    self.scene.addItem(edge)
                    self.edges.append(edge)
                    
        self.scene.update()
                    
    def update_status(self, task_id, status):
        if task_id in self.nodes:
            self.nodes[task_id].status = status
            self.nodes[task_id].update()

class DAGWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        bar = QHBoxLayout()
        self.btn_refresh = TacticalButton(I18N.t("btn_refresh_view"))
        self.btn_layout = TacticalButton(I18N.t("btn_reset_layout"))
        bar.addStretch()
        bar.addWidget(self.btn_layout)
        bar.addWidget(self.btn_refresh)
        
        self.view = DAGVisualizer()
        
        layout.addLayout(bar)
        layout.addWidget(self.view)
        
        self.btn_layout.clicked.connect(lambda: self.view.update_graph(self.view.tasks_data))
