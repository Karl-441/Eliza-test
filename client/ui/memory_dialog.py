from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, 
                             QListWidget, QListWidgetItem, QLineEdit, QLabel, QMessageBox, 
                             QScrollArea, QFrame)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QIcon

from ..framework.theme import THEME
from ..framework.i18n import I18N
from ..components import TacticalButton, TacticalFrame

class MemoryItemWidget(QWidget):
    def __init__(self, memory_data, layer_name, delete_callback, parent=None):
        super().__init__(parent)
        self.memory_id = memory_data.get("id")
        self.layer_name = layer_name
        self.delete_callback = delete_callback
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        content = memory_data.get("content", "")
        if len(content) > 100:
            content = content[:97] + "..."
            
        self.lbl_content = QLabel(content)
        self.lbl_content.setStyleSheet(f"color: {THEME.get_color('text_primary')}; font-family: '{THEME.fonts['family_code']}';")
        self.lbl_content.setWordWrap(True)
        
        self.btn_delete = TacticalButton("DEL", size="small", accent=THEME.get_color("accent_warn"))
        self.btn_delete.setFixedSize(50, 30)
        self.btn_delete.clicked.connect(self.on_delete)
        
        layout.addWidget(self.lbl_content, 1)
        layout.addWidget(self.btn_delete)
        
    def on_delete(self):
        self.delete_callback(self.layer_name, self.memory_id)

class MemoryListWidget(QWidget):
    def __init__(self, layer_name, client, parent=None):
        super().__init__(parent)
        self.layer_name = layer_name
        self.client = client
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                background-color: {THEME.hex_to_rgba(THEME.get_color('background_secondary'), 0.5)};
                margin-bottom: 4px;
                border-radius: 4px;
            }}
            QListWidget::item:hover {{
                background-color: {THEME.hex_to_rgba(THEME.get_color('accent'), 0.1)};
            }}
        """)
        
        layout.addWidget(self.list_widget)
        self.refresh()
        
    def refresh(self, query=None):
        self.list_widget.clear()
        
        if query:
            results = self.client.search_memories(self.layer_name, query)
            # Results format: [{"memory": {...}, "similarity": 0.9}]
            memories = [r.get("memory", {}) for r in results]
        else:
            data = self.client.get_memories(self.layer_name)
            memories = data.get("memories", [])
            
        for mem in memories:
            item = QListWidgetItem(self.list_widget)
            widget = MemoryItemWidget(mem, self.layer_name, self.delete_memory)
            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)
            
    def delete_memory(self, layer_name, memory_id):
        reply = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this memory?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            success = self.client.delete_memory_item(layer_name, memory_id)
            if success:
                self.refresh()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete memory.")

class MemoryManagementDialog(QDialog):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.setWindowTitle(I18N.t("memory_management_title") if hasattr(I18N, 't') else "Memory Management")
        self.setMinimumSize(800, 600)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {THEME.get_color('background')};
            }}
            QLabel {{
                color: {THEME.get_color('text_primary')};
            }}
            QTabWidget::pane {{
                border: 1px solid {THEME.get_color('border')};
                background: {THEME.get_color('background_secondary')};
            }}
            QTabBar::tab {{
                background: {THEME.get_color('background')};
                color: {THEME.get_color('text_secondary')};
                padding: 8px 16px;
                border: 1px solid {THEME.get_color('border')};
                border-bottom: none;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {THEME.get_color('background_secondary')};
                color: {THEME.get_color('accent')};
                border-top: 2px solid {THEME.get_color('accent')};
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("MEMORY MATRIX")
        title.setStyleSheet(f"font-size: {THEME.fonts['size_h2']}px; font-weight: bold; color: {THEME.get_color('accent')};")
        header_layout.addWidget(title)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search memories...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME.get_color('background_secondary')};
                color: {THEME.get_color('text_primary')};
                border: 1px solid {THEME.get_color('border')};
                padding: 8px;
                border-radius: 4px;
                font-family: '{THEME.fonts['family_code']}';
            }}
            QLineEdit:focus {{
                border: 1px solid {THEME.get_color('accent')};
            }}
        """)
        self.search_input.returnPressed.connect(self.on_search)
        header_layout.addWidget(self.search_input)
        
        btn_search = TacticalButton("SEARCH", size="small")
        btn_search.clicked.connect(self.on_search)
        header_layout.addWidget(btn_search)
        
        layout.addLayout(header_layout)
        
        # Tabs
        self.tabs = QTabWidget()
        self.instinct_list = MemoryListWidget("instinct", self.client)
        self.subconscious_list = MemoryListWidget("subconscious", self.client)
        self.active_list = MemoryListWidget("active_recall", self.client)
        
        self.tabs.addTab(self.instinct_list, "Instinct")
        self.tabs.addTab(self.subconscious_list, "Subconscious")
        self.tabs.addTab(self.active_list, "Active Recall")
        
        layout.addWidget(self.tabs)
        
        # Footer
        footer_layout = QHBoxLayout()
        btn_refresh = TacticalButton("REFRESH", size="small")
        btn_refresh.clicked.connect(self.on_refresh)
        
        btn_close = TacticalButton("CLOSE", size="small", accent=THEME.get_color('text_secondary'))
        btn_close.clicked.connect(self.accept)
        
        footer_layout.addWidget(btn_refresh)
        footer_layout.addStretch()
        footer_layout.addWidget(btn_close)
        
        layout.addLayout(footer_layout)
        
    def on_search(self):
        query = self.search_input.text().strip()
        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, MemoryListWidget):
            current_widget.refresh(query)
            
    def on_refresh(self):
        self.search_input.clear()
        self.instinct_list.refresh()
        self.subconscious_list.refresh()
        self.active_list.refresh()
