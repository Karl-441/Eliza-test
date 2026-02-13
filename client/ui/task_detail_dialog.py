from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QFrame, QScrollArea, QWidget)
from PyQt5.QtCore import Qt
from ..framework.theme import THEME
from ..framework.i18n import I18N
from ..components import TacticalButton, TacticalFrame

class TaskDetailDialog(QDialog):
    def __init__(self, parent=None, task_data=None):
        super().__init__(parent)
        self.task_data = task_data or {}
        self.setWindowTitle(I18N.t("window_title_task_detail"))
        self.setMinimumSize(600, 500)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Main Frame
        self.frame = TacticalFrame()
        self.layout.addWidget(self.frame)
        
        self.content_layout = QVBoxLayout(self.frame)
        
        # Header
        self.header_layout = QHBoxLayout()
        title_prefix = I18N.t("task_detail_title_prefix")
        task_id = self.task_data.get('id', I18N.t("task_detail_unknown"))
        self.lbl_title = QLabel(f"{title_prefix}{task_id}")
        self.lbl_title.setStyleSheet(f"color: {THEME.get_color('accent')}; font-size: 18px; font-weight: bold;")
        
        self.btn_close = TacticalButton("X")
        self.btn_close.setFixedSize(30, 30)
        self.btn_close.set_accent_color(THEME.get_color('error'))
        self.btn_close.clicked.connect(self.accept)
        
        self.header_layout.addWidget(self.lbl_title)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.btn_close)
        self.content_layout.addLayout(self.header_layout)
        
        # Content
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"background: transparent; border: none;")
        self.content_widget = QWidget()
        self.scroll.setWidget(self.content_widget)
        self.form_layout = QVBoxLayout(self.content_widget)
        
        self.add_section(I18N.t("task_section_description"), self.task_data.get("content", self.task_data.get("description", "")))
        self.add_section(I18N.t("task_section_status"), self.task_data.get("status", "").upper())
        
        role = self.task_data.get("performer") or self.task_data.get("target_role") or self.task_data.get("role", "Unknown")
        self.add_section(I18N.t("task_section_role"), role)
        
        self.add_section(I18N.t("task_section_deps"), ", ".join(self.task_data.get("dependencies", [])))
        
        if "model" in self.task_data:
             self.add_section(I18N.t("task_section_model"), self.task_data["model"])
        
        if "duration" in self.task_data:
             try:
                 dur = float(self.task_data["duration"])
                 self.add_section(I18N.t("task_section_duration"), f"{dur:.2f}s")
             except:
                 pass
        
        if self.task_data.get("status") == "failed":
             self.add_section(I18N.t("task_section_error"), self.task_data.get("error", "Unknown Error"))
        else:
             self.add_section(I18N.t("task_section_output"), self.task_data.get("output", self.task_data.get("result", "")) or I18N.t("task_output_none"))
        
        self.content_layout.addWidget(self.scroll)
        
    def add_section(self, title, content):
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"color: {THEME.get_color('text_secondary')}; font-size: 12px; font-weight: bold; margin-top: 10px;")
        
        txt_content = QTextEdit()
        txt_content.setReadOnly(True)
        txt_content.setPlainText(str(content))
        txt_content.setStyleSheet(f"""
            QTextEdit {{
                background-color: {THEME.hex_to_rgba(THEME.get_color('background_secondary'), 0.5)};
                color: {THEME.get_color('text_primary')};
                border: 1px solid {THEME.get_color('border')};
                font-family: {THEME.fonts['family_code']};
                padding: 5px;
            }}
        """)
        # Auto-height adjustment logic could go here, but fixed height is safer for now
        txt_content.setMaximumHeight(100 if len(str(content)) < 200 else 200)
        
        self.form_layout.addWidget(lbl_title)
        self.form_layout.addWidget(txt_content)
