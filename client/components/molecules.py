from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QMenu, QApplication, 
                             QPlainTextEdit, QTextEdit, QInputDialog, QMessageBox, QFileDialog, QWidget, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QTextCursor
from ..framework.theme import THEME
from ..framework.i18n import I18N
from .atoms import TacticalButton

class TacticalFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.NoFrame)
        self.glow_alpha = 100
        self.glow_dir = 5
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.pulse_glow)
        self.timer.start(100)
        
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
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
        
        painter.fillRect(rect, QColor(0, 0, 0, 100))
        
        accent = QColor(THEME.get_color("accent"))
        glow_color = QColor(accent)
        glow_color.setAlpha(self.glow_alpha)
        
        painter.setPen(QPen(glow_color, 4))
        l = 15
        
        # Corners
        painter.drawLine(0, 0, l, 0)
        painter.drawLine(0, 0, 0, l)
        painter.drawLine(rect.width(), 0, rect.width()-l, 0)
        painter.drawLine(rect.width(), 0, rect.width(), l)
        painter.drawLine(0, rect.height(), l, rect.height())
        painter.drawLine(0, rect.height(), 0, rect.height()-l)
        painter.drawLine(rect.width(), rect.height(), rect.width()-l, rect.height())
        painter.drawLine(rect.width(), rect.height(), rect.width(), rect.height()-l)
        
        painter.setPen(QPen(accent, 2))
        painter.drawLine(0, 0, l, 0)
        painter.drawLine(0, 0, 0, l)
        painter.drawLine(rect.width(), 0, rect.width()-l, 0)
        painter.drawLine(rect.width(), 0, rect.width(), l)
        painter.drawLine(0, rect.height(), l, rect.height())
        painter.drawLine(0, rect.height(), 0, rect.height()-l)
        painter.drawLine(rect.width(), rect.height(), rect.width()-l, rect.height())
        painter.drawLine(rect.width(), rect.height(), rect.width(), rect.height()-l)

class ChatBubble(QFrame):
    def __init__(self, text, is_user, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(THEME.spacing["s"], THEME.spacing["xs"], THEME.spacing["s"], THEME.spacing["xs"])
        
        self.bubble = QLabel(text)
        self.bubble.setWordWrap(True)
        self.bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.bubble.setFont(THEME.get_font("body"))
        
        import datetime
        time_str = datetime.datetime.now().strftime("%H:%M")
        self.time_lbl = QLabel(time_str)
        self.time_lbl.setStyleSheet(f"color: {THEME.get_color('text_secondary')}; font-size: {THEME.fonts['size_small']}px;")
        
        accent = THEME.get_color("accent")
        bg_tertiary = THEME.get_color("background_tertiary")
        text_color = THEME.get_color("text_primary")
        border_color = THEME.get_color("border")
        
        if is_user:
            self.layout.addStretch()
            self.layout.addWidget(self.time_lbl)
            self.layout.addWidget(self.bubble)
            self.bubble.setStyleSheet(f"""
                background-color: {THEME.hex_to_rgba(accent, 0.8)};
                color: {THEME.get_color('background')};
                border-radius: 2px;
                padding: 8px 12px;
                border-bottom-left-radius: 10px;
                border: 1px solid {accent};
            """)
        else:
            self.layout.addWidget(self.bubble)
            self.layout.addWidget(self.time_lbl)
            self.layout.addStretch()
            self.bubble.setStyleSheet(f"""
                background-color: {THEME.hex_to_rgba(bg_tertiary, 0.9)};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 2px;
                padding: 8px 12px;
                border-bottom-right-radius: 10px;
                border-left: 3px solid {accent};
            """)
            
        self.bubble.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.bubble.setMinimumWidth(50)
        self.bubble.setMaximumWidth(800)

    def resizeEvent(self, event):
        if self.parent():
            target_width = int(self.parent().width() * 0.75)
            self.bubble.setMaximumWidth(target_width)
        super().resizeEvent(event)

class StatusIndicator(QWidget):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(THEME.spacing["s"], 2, THEME.spacing["s"], 2)
        
        self.dot = QFrame()
        self.dot.setFixedSize(8, 8)
        self.dot.setStyleSheet(f"background-color: {THEME.get_color('text_secondary')}; border-radius: 4px;")
        
        self.label = QLabel(label_text)
        self.label.setFont(THEME.get_font("code"))
        self.label.setStyleSheet(f"color: {THEME.get_color('text_secondary')}; font-weight: bold;")
        
        self.value_label = QLabel(I18N.t("status_offline"))
        self.value_label.setFont(THEME.get_font("code"))
        self.value_label.setStyleSheet(f"color: {THEME.get_color('text_secondary')}; font-weight: bold;")
        
        self.layout.addWidget(self.dot)
        self.layout.addWidget(self.label)
        self.layout.addStretch()
        self.layout.addWidget(self.value_label)
        
    def set_status(self, status, message=""):
        status_key = status.upper()
        # Translate for display
        display_status = I18N.t(f"status_{status.lower()}", status_key)
        self.value_label.setText(display_status)
        
        color = THEME.get_color("text_secondary")
        if status_key == "ONLINE":
            color = THEME.get_color("success")
        elif status_key == "OFFLINE":
            color = THEME.get_color("error")
        elif status_key == "UNKNOWN":
            color = THEME.get_color("warning")
            
        self.dot.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
        self.value_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        
        if message:
            self.setToolTip(message)

class LogViewer(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumHeight(150)
        self.logs = []
        self.filter_level = "ALL"
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {THEME.hex_to_rgba(THEME.get_color('background_tertiary'), 0.9)};
                color: {THEME.get_color('text_primary')};
                font-family: {THEME.fonts['family_code']};
                border: 1px solid {THEME.get_color('border')};
                border-left: 3px solid {THEME.get_color('accent')};
            }}
        """)
    def add_log(self, level, message):
        import datetime
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        entry = {'timestamp': time_str, 'level': level, 'message': message}
        self.logs.append(entry)
        if self.filter_level == "ALL" or self.filter_level == level:
            self.append_log_html(entry)
    def append_log_html(self, entry):
        color = THEME.get_color('text_secondary')
        if entry['level'] == "WARN": color = THEME.get_color('accent')
        if entry['level'] == "ERROR": color = THEME.get_color('warning')
        
        level_display = I18N.t(f"log_level_{entry['level'].lower()}", entry['level'])
        html = f'<div style="margin-bottom: 2px;"><span style="color:{THEME.get_color("text_secondary")};">[{entry["timestamp"]}]</span> <span style="color:{color}; font-weight:bold;">[{level_display}]</span> {entry["message"]}</div>'
        self.appendHtml(html)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
    def set_filter(self, level):
        self.filter_level = level
        self.clear()
        for entry in self.logs:
            if self.filter_level == "ALL" or self.filter_level == entry['level']:
                self.append_log_html(entry)
    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        action_export = menu.addAction("Export Log")
        action_export.triggered.connect(self.export_log)
        action_search = menu.addAction("Search Log")
        action_search.triggered.connect(self.search_log)
        action_clear = menu.addAction("Clear Log")
        action_clear.triggered.connect(self.clear_logs)
        menu.exec_(event.globalPos())
    def clear_logs(self):
        self.logs = []
        self.clear()
    def search_log(self):
        text, ok = QInputDialog.getText(self, "Search Log", "Find:")
        if ok and text:
            if not self.find(text):
                self.moveCursor(QTextCursor.Start)
                if not self.find(text):
                    QMessageBox.information(self, "Search", "Text not found.")
    def export_log(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Export Log", "", "Text Files (*.txt);;All Files (*)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    for entry in self.logs:
                        f.write(f"[{entry['timestamp']}][{entry['level']}] {entry['message']}\n")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not save log: {e}")

class ChatInput(QTextEdit):
    enterPressed = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(False)
        self.textChanged.connect(self.update_counter)
        self.send_on_enter = True
        self.default_style = f"""
            QTextEdit {{
                background-color: {THEME.hex_to_rgba(THEME.get_color('background_tertiary'), 0.5)};
                color: {THEME.get_color('text_primary')};
                border: 1px solid {THEME.get_color('border')};
                border-left: 2px solid {THEME.get_color('accent_dim')};
                padding: {THEME.spacing['s']}px;
                font-family: "{THEME.fonts['family_main']}";
                font-size: {THEME.fonts['size_body']}px;
            }}
            QTextEdit:focus {{
                border: 1px solid {THEME.get_color('accent')};
                border-left: 2px solid {THEME.get_color('accent')};
                background-color: {THEME.hex_to_rgba(THEME.get_color('background_tertiary'), 0.7)};
            }}
        """
        self.command_style = f"""
            QTextEdit {{
                background-color: {THEME.hex_to_rgba(THEME.get_color('background_tertiary'), 0.6)};
                color: {THEME.get_color('accent')};
                border: 1px solid {THEME.get_color('accent')};
                border-left: 2px solid {THEME.get_color('accent')};
                padding: {THEME.spacing['s']}px;
                font-family: {THEME.fonts['family_code']};
                font-size: {THEME.fonts['size_body']}px;
            }}
        """
        self.setStyleSheet(self.default_style)
        self.lbl_counter = QLabel("0/2000", self)
        self.lbl_counter.setStyleSheet(f"color: {THEME.get_color('text_secondary')}; font-family: {THEME.fonts['family_code']}; font-size: {THEME.fonts['size_small']}px; background: transparent;")
        self.lbl_counter.setAlignment(Qt.AlignRight)
        self.lbl_counter.hide()
        self.lbl_cmd_hint = QLabel("COMMAND MODE", self)
        self.lbl_cmd_hint.setStyleSheet(f"color: {THEME.get_color('accent')}; font-family: {THEME.fonts['family_code']}; font-size: {THEME.fonts['size_small']}px; font-weight: bold; background: transparent;")
        self.lbl_cmd_hint.hide()
        self.is_command_mode = False
    def set_send_on_enter(self, enable):
        self.send_on_enter = enable
        self.update()
    def update_counter(self):
        text = self.toPlainText()
        count = len(text)
        self.lbl_counter.setText(f"{count}/2000")
        self.lbl_counter.adjustSize()
        if count > 2000:
            self.lbl_counter.setStyleSheet(f"color: {THEME.get_color('warning')}; font-family: {THEME.fonts['family_code']}; font-size: {THEME.fonts['size_small']}px; font-weight: bold;")
        else:
            self.lbl_counter.setStyleSheet(f"color: {THEME.get_color('text_secondary')}; font-family: {THEME.fonts['family_code']}; font-size: {THEME.fonts['size_small']}px;")
        if count > 0:
            self.lbl_counter.show()
        else:
            self.lbl_counter.hide()
        if text.startswith("/"):
            if not self.is_command_mode:
                self.is_command_mode = True
                self.setStyleSheet(self.command_style)
                self.lbl_cmd_hint.show()
        else:
            if self.is_command_mode:
                self.is_command_mode = False
                self.setStyleSheet(self.default_style)
                self.lbl_cmd_hint.hide()
        self.lbl_counter.move(self.viewport().width() - self.lbl_counter.width() - THEME.spacing['s'], THEME.spacing['xs'])
        self.lbl_cmd_hint.move(THEME.spacing['s'], THEME.spacing['xs'])
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            modifiers = event.modifiers()
            if self.send_on_enter:
                if modifiers & (Qt.ShiftModifier | Qt.ControlModifier):
                    self.insertPlainText("\n")
                else:
                    if len(self.toPlainText()) <= 2000:
                        self.enterPressed.emit()
            else:
                if modifiers & Qt.ControlModifier:
                    if len(self.toPlainText()) <= 2000:
                        self.enterPressed.emit()
                else:
                    super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing)
        if self.send_on_enter:
            hint_text = I18N.t("input_hint_send")
        else:
            hint_text = I18N.t("input_hint_send_ctrl")
        font = THEME.get_font("small")
        painter.setFont(font)
        metrics = painter.fontMetrics()
        text_width = metrics.width(hint_text)
        text_height = metrics.height()
        x = self.viewport().width() - text_width - THEME.spacing['m']
        y = self.viewport().height() - THEME.spacing['m']
        painter.setPen(QColor(THEME.get_color('text_secondary')))
        painter.drawText(x, y, hint_text)

class TacticalButtonBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(THEME.spacing['s'])
        
        self.btn_settings = self.create_btn("SETTINGS")
        self.layout.addWidget(self.btn_settings)
        
        self.btn_tts = self.create_btn("TTS: OFF", checkable=True)
        self.layout.addWidget(self.btn_tts)
        
        self.btn_search = self.create_btn("NET: OFF", checkable=True)
        self.layout.addWidget(self.btn_search)
        
        self.btn_multi_agent = self.create_btn("MULTI-AGENT")
        self.btn_multi_agent.set_accent_color(THEME.get_color('info'))
        self.layout.addWidget(self.btn_multi_agent)
        
        self.btn_memory = self.create_btn("MEMORY")
        self.btn_memory.set_accent_color(THEME.get_color('warning'))
        self.layout.addWidget(self.btn_memory)
        
        self.layout.addStretch()
        
        self.btn_voice = self.create_btn("VOICE")
        self.layout.addWidget(self.btn_voice)
        
        self.btn_clear = self.create_btn("PURGE")
        self.btn_clear.set_accent_color(THEME.get_color('error'))
        self.layout.addWidget(self.btn_clear)
        
        self.btn_send = self.create_btn("SEND")
        self.btn_send.set_accent_color(THEME.get_color('success'))
        self.layout.addWidget(self.btn_send)
    def create_btn(self, text, checkable=False):
        btn = TacticalButton(text, parent=self)
        if checkable:
            btn.setCheckable(True)
        if hasattr(btn, 'shadow'):
            btn.shadow.setBlurRadius(15)
        btn.raise_()
        return btn
