
import os
import sys
import argparse

TEMPLATE_ATOM = """from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor
from ..framework.theme import THEME

class {name}(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 100)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(THEME.get_color('BACKGROUND_SECONDARY')))
        
        # Draw accent border
        pen = painter.pen()
        pen.setColor(QColor(THEME.get_color('ACCENT_COLOR')))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))
"""

TEMPLATE_MOLECULE = """from PyQt5.QtWidgets import QWidget, QVBoxLayout
from ..atoms import TacticalButton
from ..framework.theme import THEME

class {name}(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.btn = TacticalButton("Action", self)
        self.layout.addWidget(self.btn)
"""

def create_component(name, type_):
    base_dir = os.path.join(os.path.dirname(__file__), '../components')
    if type_ == 'atom':
        target_file = os.path.join(base_dir, 'atoms.py') # Append to atoms.py
        template = TEMPLATE_ATOM
    elif type_ == 'molecule':
        target_file = os.path.join(base_dir, 'molecules.py')
        template = TEMPLATE_MOLECULE
    else:
        print(f"Unknown type: {type_}")
        return

    # Check if we should append or create new file
    # For this framework, we put classes in atoms.py/molecules.py
    # So we append.
    
    code = template.format(name=name)
    
    try:
        with open(target_file, 'a', encoding='utf-8') as f:
            f.write("\n" + code + "\n")
        print(f"Successfully added {name} to {target_file}")
    except Exception as e:
        print(f"Error writing to file: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scaffold new UI components')
    parser.add_argument('name', help='Name of the component class')
    parser.add_argument('--type', choices=['atom', 'molecule'], default='atom', help='Component type')
    
    args = parser.parse_args()
    create_component(args.name, args.type)
