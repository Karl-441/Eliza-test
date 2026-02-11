from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel, QFrame, QScrollArea, QSizePolicy, QCheckBox, QInputDialog, QMessageBox, QDialog, QFormLayout, QSpinBox, QDoubleSpinBox, QFileDialog, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QTabWidget, QListWidget, QListWidgetItem, QSplitter, QPlainTextEdit, QSlider, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QStackedLayout, QScroller, QScrollerProperties, QApplication, QMenu, QGridLayout)
from PyQt5.QtCore import Qt, QSize, QTimer, QThread, pyqtSignal, QUrl, QPropertyAnimation, QEasingCurve, QRect, QParallelAnimationGroup, QSettings, pyqtProperty
from PyQt5.QtGui import QPixmap, QFont, QColor, QPalette, QPainter, QBrush, QPen, QImage, QLinearGradient, QTextCursor, QTextCharFormat, QTextDocument
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import os
import json
import tempfile

from ..api_client import APIClient
from ..core.theme_manager import ThemeManager
from ..core.voice_system import VoiceSystem
from .voice_widget import VoiceControlWidget
from .settings_dialog import SettingsDialog
from .multi_agent_ui import MultiAgentWidget

# New Architecture Imports
from ..framework.theme import THEME
from ..components import (
    TacticalButton, TacticalFrame, ParticleBackground, RadarChart, 
    ChatBubble, StatusIndicator, LogViewer, ChatInput, TacticalButtonBar, BootOverlay
)

class Worker(QThread):
    finished = pyqtSignal(dict)
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result if isinstance(result, dict) else {"data": result})
        except Exception as e:
            self.finished.emit({"error": str(e)})

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ELIZA // TACTICAL ASSISTANT")
        self.settings = QSettings("Eliza", "Client")
        self.setMinimumSize(700, 600)
        
        # Resolution
        res_text = self.settings.value("resolution", "1280x720 (HD)")
        self.apply_window_size(res_text)

        assets_dir = os.path.join(os.path.dirname(__file__), "../assets")
        griffin_path = os.path.join(assets_dir, "griffin_logo.png")
        sf_path = os.path.join(assets_dir, "sf_logo.jpg")
        
        self.client = APIClient()
        self.theme_manager = ThemeManager(self.client)
        self.theme_manager.theme_updated.connect(self.on_theme_updated)
        
        self.search_history = self.settings.value("search_history", [])
        if not isinstance(self.search_history, list):
            self.search_history = []
        self.is_searching = False
        self.available_voices = {}
        
        self.tts_speed = float(self.settings.value("tts_speed", 1.0))
        self.tts_volume = float(self.settings.value("tts_volume", 1.0))
        self.tts_voice = self.settings.value("tts_voice", "default")
        self.custom_avatar_path = self.settings.value("avatar_path", "")
        self.continuous_mode = False
        
        self.player = QMediaPlayer()
        self.player.stateChanged.connect(self.on_media_state_changed)
        
        # Voice System
        ws_base = self.client.base_url.replace("http", "ws").replace("https", "wss")
        self.voice_system = VoiceSystem(api_url=f"{ws_base}/audio/stream")
        self.voice_system.text_received.connect(self.on_voice_text)
        self.voice_system.wake_detected.connect(self.on_wake_word)
        self.voice_system.status_changed.connect(lambda s: self.add_system_message(f"VOICE: {s}"))
        
        # Workers
        self.worker = None
        self.status_worker = None
        self.check_worker = None
        self.tts_worker = None
        self.config_worker = None
        
        self.central_widget = QWidget()
        self.central_widget.setObjectName("MainWidget")
        self.setCentralWidget(self.central_widget)
        
        self.stack_layout = QStackedLayout(self.central_widget)
        self.stack_layout.setStackingMode(QStackedLayout.StackAll)
        
        self.bg_particles = ParticleBackground(parent=self.central_widget, griffin_logo=griffin_path, sf_logo=sf_path)
        self.stack_layout.addWidget(self.bg_particles)
        
        self.content_widget = QWidget()
        self.content_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.stack_layout.addWidget(self.content_widget)
        self.content_widget.raise_()
        
        self.multi_agent_widget = MultiAgentWidget(parent=self.central_widget, client=self.client)
        self.multi_agent_widget.hide()
        self.multi_agent_widget.close_requested.connect(self.hide_multi_agent_mode)
        self.stack_layout.addWidget(self.multi_agent_widget)
        
        self.main_layout = QHBoxLayout(self.content_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.setup_left_panel()
        self.setup_right_panel()
        
        self.main_layout.setStretchFactor(self.left_panel, 3)
        self.main_layout.setStretchFactor(self.right_panel, 7)
        
        self.apply_styles()
        
        self._ui_font_size = int(self.settings.value("ui_font_size_override", 0)) or self.compute_target_font_size()
        # THEME.set_base_font_size(self._ui_font_size) # TODO: Implement in ThemeEngine if needed
        
        self.add_system_message("Initializing Neural Link...")
        QTimer.singleShot(1000, self.check_server)
        
        self.center_window()
        
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_server_status)
        self.status_timer.start(2000)
        
        self.local_timer = QTimer(self)
        self.local_timer.timeout.connect(self.update_local_status)
        self.local_timer.start(200)

        self.boot_overlay = BootOverlay(self)
        self.boot_overlay.resize(self.size())
        self.boot_overlay.finished.connect(self.boot_overlay.hide)
        self.boot_overlay.show()
        
        self.anim_font = QPropertyAnimation(self, b"ui_font_size")
        self.anim_font.setDuration(THEME.anim["duration_normal"])
        self.anim_font.setEasingCurve(QEasingCurve.OutCubic)

    def center_window(self):
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def compute_target_font_size(self):
        screen = QApplication.primaryScreen()
        dpi = 96.0
        if screen:
            dpi = float(screen.logicalDotsPerInch())
        w = max(1, self.width())
        h = max(1, self.height())
        base = int(12 + (min(w, h) / 1280.0) * 12)
        scaled = int(base * (dpi / 96.0))
        return max(12, min(24, scaled))

    def set_ui_font_size(self, val):
        self._ui_font_size = int(val)
        # THEME.set_base_font_size(self._ui_font_size)
        self.apply_styles()

    def get_ui_font_size(self):
        return int(self._ui_font_size)

    ui_font_size = pyqtProperty(int, fget=get_ui_font_size, fset=set_ui_font_size)

    def apply_window_size(self, size_text):
        if "Fullscreen" in size_text:
            if not self.isFullScreen():
                self.showFullScreen()
        else:
            if self.isFullScreen():
                self.showNormal()
            screen_geo = QApplication.desktop().availableGeometry()
            max_w = screen_geo.width()
            max_h = screen_geo.height()
            target_size = QSize(1280, 720)
            if "1920x1080" in size_text:
                target_size = QSize(1920, 1080)
            elif "1366x768" in size_text:
                target_size = QSize(1366, 768)
            elif "1280x720" in size_text:
                target_size = QSize(1280, 720)
            elif "1024x768" in size_text:
                target_size = QSize(1024, 768)
            elif "800x600" in size_text:
                target_size = QSize(800, 600)
            target_size.setWidth(min(target_size.width(), max_w))
            target_size.setHeight(min(target_size.height(), max_h))
            self.resize(target_size)

    def resizeEvent(self, event):
        if hasattr(self, 'boot_overlay') and self.boot_overlay.isVisible():
            self.boot_overlay.resize(self.size())
            self.boot_overlay.raise_()
        if hasattr(self, 'content_widget'):
            self.content_widget.resize(self.size())
        if hasattr(self, 'btn_scroll_bottom'):
            self.update_scroll_button_pos()
            self.btn_scroll_bottom.raise_()
        if hasattr(self, 'bg_particles'):
            self.bg_particles.resize(self.size())
            self.bg_particles.lower()
        if int(self.settings.value("ui_font_size_override", 0)) == 0:
            target = self.compute_target_font_size()
            if target != self._ui_font_size:
                self.anim_font.stop()
                self.anim_font.setStartValue(self._ui_font_size)
                self.anim_font.setEndValue(target)
                self.anim_font.start()
        super().resizeEvent(event)

    def closeEvent(self, event):
        if self.windowOpacity() > 0:
            event.ignore()
            self.anim_close = QPropertyAnimation(self, b"windowOpacity")
            self.anim_close.setDuration(800)
            self.anim_close.setStartValue(1)
            self.anim_close.setEndValue(0)
            self.anim_close.setEasingCurve(QEasingCurve.InExpo)
            self.anim_close.finished.connect(self.force_close)
            self.anim_close.start()
        else:
            event.accept()

    def force_close(self):
        if self.status_timer.isActive():
            self.status_timer.stop()
        if self.local_timer.isActive():
            self.local_timer.stop()
        for w in [self.worker, self.status_worker, self.check_worker, self.tts_worker, self.config_worker]:
            if w and w.isRunning():
                w.quit()
                w.wait()
        self.setAttribute(Qt.WA_DontShowOnScreen)
        self.close()

    def setup_left_panel(self):
        self.left_panel = QWidget()
        self.left_panel.setObjectName("LeftPanel")
        layout = QVBoxLayout(self.left_panel)
        layout.setContentsMargins(THEME.spacing["l"], THEME.spacing["l"], THEME.spacing["l"], THEME.spacing["l"])
        
        self.char_frame = TacticalFrame()
        frame_layout = QVBoxLayout(self.char_frame)
        frame_layout.setContentsMargins(THEME.spacing["s"], THEME.spacing["s"], THEME.spacing["s"], THEME.spacing["s"])
        
        lbl_adjutant = QLabel("ADJUTANT // TACTICAL DOLL")
        lbl_adjutant.setStyleSheet(f"color: {THEME.get_color('accent')}; font-weight: bold; font-size: {THEME.fonts['size_small']}px; letter-spacing: 2px;")
        frame_layout.addWidget(lbl_adjutant)
        
        self.char_image = QLabel()
        self.char_image.setAlignment(Qt.AlignCenter)
        self.char_image.setFixedSize(250, 350)
        self.char_image.setStyleSheet(f"background-color: {THEME.get_color('background_secondary')}; border: 1px solid {THEME.get_color('accent_dim')};")
        self.load_avatar_image()
        frame_layout.addWidget(self.char_image, 0, Qt.AlignCenter)
        
        btn_upload = TacticalButton("CHANGE ADJUTANT", parent=self)
        btn_upload.clicked.connect(self.change_avatar)
        frame_layout.addWidget(btn_upload)
        
        layout.addWidget(self.char_frame)
        
        log_frame = TacticalFrame()
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(THEME.spacing["s"], THEME.spacing["s"], THEME.spacing["s"], THEME.spacing["s"])
        
        log_header_layout = QHBoxLayout()
        log_lbl = QLabel("MISSION LOGS")
        log_lbl.setStyleSheet(f"color: {THEME.get_color('accent')}; font-weight: bold; letter-spacing: 1px;")
        
        self.log_filter = QComboBox()
        self.log_filter.addItems(["ALL", "INFO", "WARN", "ERROR"])
        self.log_filter.setStyleSheet(f"background: {THEME.get_color('background_secondary')}; color: {THEME.get_color('text_primary')}; border: 1px solid {THEME.get_color('accent_dim')}; padding: 2px;")
        self.log_filter.currentTextChanged.connect(self.on_log_filter_changed)
        
        log_header_layout.addWidget(log_lbl)
        log_header_layout.addStretch()
        log_header_layout.addWidget(self.log_filter)
        log_layout.addLayout(log_header_layout)
        
        self.log_viewer = LogViewer()
        self.log_viewer.setFrameShape(QFrame.NoFrame)
        self.log_viewer.add_log("INFO", "Mission Logs Initialized. Monitoring system events...")
        log_layout.addWidget(self.log_viewer)
        
        layout.addWidget(log_frame)
        
        self.status_container = TacticalFrame()
        status_layout = QVBoxLayout(self.status_container)
        status_layout.setSpacing(THEME.spacing["s"])
        status_layout.setContentsMargins(THEME.spacing["m"], THEME.spacing["m"], THEME.spacing["m"], THEME.spacing["m"])
        
        status_header = QHBoxLayout()
        self.status_title = QLabel("SYSTEM VITALS")
        self.status_title.setStyleSheet(f"color: {THEME.get_color('accent')}; font-weight: bold; letter-spacing: 1px;")
        
        btn_refresh = QPushButton("⟳")
        btn_refresh.setFixedSize(24, 24)
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(f"background: transparent; color: {THEME.get_color('accent')}; border: none; font-size: 16px; font-weight: bold;")
        btn_refresh.setToolTip("Refresh Status")
        btn_refresh.clicked.connect(self.update_server_status)
        
        status_header.addWidget(self.status_title)
        status_header.addStretch()
        status_header.addWidget(btn_refresh)
        status_layout.addLayout(status_header)
        
        grid_layout = QGridLayout()
        self.status_agent = StatusIndicator("AGENT")
        self.status_agent.set_status("online")
        self.status_server = StatusIndicator("UPLINK")
        self.status_llm = StatusIndicator("NEURAL")
        self.status_tts = StatusIndicator("VOCAL")
        
        grid_layout.addWidget(self.status_agent, 0, 0)
        grid_layout.addWidget(self.status_server, 0, 1)
        grid_layout.addWidget(self.status_llm, 1, 0)
        grid_layout.addWidget(self.status_tts, 1, 1)
        status_layout.addLayout(grid_layout)
        
        self.radar = RadarChart(parent=self.status_container)
        status_layout.addWidget(self.radar, 0, Qt.AlignCenter)
        
        self.lbl_last_check = QLabel("SYNC: --:--:--")
        self.lbl_last_check.setStyleSheet(f"color: {THEME.get_color('text_secondary')}; font-size: {THEME.fonts['size_small']}px; margin-top: 4px; font-family: {THEME.fonts['family_code']};")
        self.lbl_last_check.setAlignment(Qt.AlignRight)
        status_layout.addWidget(self.lbl_last_check)
        
        layout.addStretch()
        layout.addWidget(self.status_container)
        
        self.main_layout.addWidget(self.left_panel)

    def setup_right_panel(self):
        self.right_panel = QWidget()
        self.right_panel.setObjectName("RightPanel")
        layout = QVBoxLayout(self.right_panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        top_bar = TacticalFrame()
        top_bar.setFixedHeight(60) # Header Height
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(THEME.spacing["l"], 0, THEME.spacing["l"], 0)
        
        header_title = QLabel("COMMAND CENTER")
        header_title.setStyleSheet(f"color: {THEME.get_color('accent')}; font-size: {THEME.fonts['size_h2']}px; font-weight: bold; letter-spacing: 2px;")
        
        self.btn_chat_multi = QPushButton("CHAT-MULTI")
        self.btn_chat_multi.setFixedHeight(32)
        self.btn_chat_multi.setCursor(Qt.PointingHandCursor)
        self.btn_chat_multi.setStyleSheet(f"background: transparent; color: {THEME.get_color('accent')}; border: 1px solid {THEME.get_color('accent_dim')}; padding: 0 12px; border-radius: 16px;")
        self.btn_chat_multi.setToolTip("切换聊天/多智能体模式")
        self.btn_chat_multi.clicked.connect(self.toggle_chat_multi_mode)
        
        btn_theme = QPushButton("☀/☾")
        btn_theme.setFixedSize(32, 32)
        btn_theme.setCursor(Qt.PointingHandCursor)
        btn_theme.setStyleSheet(f"background: transparent; color: {THEME.get_color('accent')}; border: 1px solid {THEME.get_color('accent_dim')}; border-radius: 16px;")
        btn_theme.clicked.connect(self.toggle_theme)
        
        lbl_logo = QLabel()
        lbl_logo.setFixedSize(THEME.spacing["l"], THEME.spacing["l"])
        lbl_logo.setScaledContents(True)
        
        top_layout.addWidget(lbl_logo)
        top_layout.addWidget(header_title)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_chat_multi)
        top_layout.addWidget(btn_theme)
        
        layout.addWidget(top_bar)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        QScroller.grabGesture(self.scroll_area.viewport(), QScroller.LeftMouseButtonGesture)
        
        self.chat_history = QWidget()
        self.chat_history.setObjectName("ChatHistory")
        self.chat_layout = QVBoxLayout(self.chat_history)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setContentsMargins(THEME.spacing["l"], THEME.spacing["l"], THEME.spacing["l"], THEME.spacing["l"])
        self.chat_layout.setSpacing(THEME.spacing["m"])
        
        self.scroll_area.setWidget(self.chat_history)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll_value_changed)
        
        self.unread_count = 0
        self.user_scrolled_up = False
        
        self.btn_scroll_bottom = TacticalButton("⇩ LATEST", parent=self.central_widget)
        self.btn_scroll_bottom.setFixedSize(120, 36)
        self.btn_scroll_bottom.hide()
        self.btn_scroll_bottom.clicked.connect(lambda: self.scroll_to_bottom(force=True))
        
        input_container = TacticalFrame()
        input_container.setObjectName("InputContainer")
        input_container.setMinimumHeight(150)
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(THEME.spacing["l"], THEME.spacing["m"], THEME.spacing["l"], THEME.spacing["m"])
        
        input_toolbar = QHBoxLayout()
        input_toolbar.setSpacing(THEME.spacing["s"])
        
        btn_emoji = QPushButton("☺")
        btn_emoji.setFixedSize(28, 28)
        btn_emoji.setCursor(Qt.PointingHandCursor)
        btn_emoji.setStyleSheet(f"background: transparent; color: {THEME.get_color('accent')}; border: none; font-size: 18px;")
        
        btn_attach = QPushButton("📂")
        btn_attach.setFixedSize(32, 32)
        btn_attach.setCursor(Qt.PointingHandCursor)
        btn_attach.setStyleSheet(f"background: transparent; color: {THEME.get_color('accent')}; border: none; font-size: 20px;")
        btn_attach.clicked.connect(self.attach_file)
        
        self.chk_enter_send = QCheckBox("Enter to Send")
        self.chk_enter_send.setChecked(True)
        self.chk_enter_send.setStyleSheet(f"color: {THEME.get_color('text_secondary')}; font-size: 12px;")
        self.chk_enter_send.stateChanged.connect(self.toggle_enter_behavior)
        
        input_toolbar.addWidget(btn_emoji)
        input_toolbar.addWidget(btn_attach)
        input_toolbar.addStretch()
        input_toolbar.addWidget(self.chk_enter_send)
        
        input_layout.addLayout(input_toolbar)
        
        self.input_box = ChatInput()
        self.input_box.enterPressed.connect(self.send_message)
        self.input_box.textChanged.connect(self.on_user_typing)
        input_layout.addWidget(self.input_box)
        
        self.func_bar = TacticalButtonBar(parent=input_container)
        self.btn_settings = self.func_bar.btn_settings
        self.btn_tts = self.func_bar.btn_tts
        self.btn_search = self.func_bar.btn_search
        self.btn_multi_agent = self.func_bar.btn_multi_agent
        self.btn_memory = self.func_bar.btn_memory
        self.btn_voice = self.func_bar.btn_voice
        self.btn_clear = self.func_bar.btn_clear
        self.btn_send = self.func_bar.btn_send
        
        self.btn_settings.clicked.connect(self.open_settings)
        self.btn_tts.toggled.connect(self.toggle_tts)
        self.btn_search.toggled.connect(self.toggle_net_search)
        self.btn_multi_agent.clicked.connect(self.show_multi_agent_mode)
        self.btn_memory.clicked.connect(self.manage_memory)
        self.btn_voice.clicked.connect(self.toggle_voice)
        self.btn_clear.clicked.connect(self.clear_memory_confirm)
        self.btn_send.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.func_bar)
        
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.scroll_area)
        splitter.addWidget(input_container)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        
        layout.addWidget(splitter)
        self.main_layout.addWidget(self.right_panel)

    def load_avatar_image(self):
        img_path = os.path.join(os.path.dirname(__file__), "../assets/character_normal.png")
        if self.custom_avatar_path and os.path.exists(self.custom_avatar_path):
            img_path = self.custom_avatar_path
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path)
            scaled = pixmap.scaled(200, 200, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            target = QPixmap(200, 200)
            target.fill(Qt.transparent)
            p = QPainter(target)
            p.setRenderHint(QPainter.Antialiasing)
            x = (200 - scaled.width()) // 2
            y = (200 - scaled.height()) // 2
            p.drawPixmap(x, y, scaled)
            p.end()
            self.char_image.setPixmap(target)
        else:
            self.char_image.setText("NO SIGNAL")
            self.char_image.setStyleSheet(f"color: {THEME.get_color('accent')}; font-size: {THEME.fonts['size_h1']}px; font-weight: bold; border: 1px solid {THEME.get_color('accent_dim')};")

    def toggle_theme(self):
        # TODO: Implement theme toggling in THEME engine
        # THEME.toggle() 
        self.apply_styles()
        # Recreate panels to apply new styles
        self.left_panel.hide()
        self.right_panel.hide()
        self.main_layout.removeWidget(self.left_panel)
        self.main_layout.removeWidget(self.right_panel)
        self.left_panel.deleteLater()
        self.right_panel.deleteLater()
        self.setup_left_panel()
        self.setup_right_panel()
        self.main_layout.setStretchFactor(self.left_panel, 3)
        self.main_layout.setStretchFactor(self.right_panel, 7)
        self.add_system_message("Visual theme re-calibrated.")

    def apply_styles(self):
        # Darker backgrounds for panels as requested
        bg_dark = THEME.get_color('background')
        # Simple darkening logic or use a specific color if available
        # Assuming hex strings, we can just hardcode a darker variant or use opacity
        # But let's use rgba for darkening overlay or just a darker hex if we knew it.
        # For now, let's use the theme's background_tertiary or manually darker.
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {THEME.get_color('background')};
            }}
            QWidget#LeftPanel {{
                background-color: {THEME.get_color('background_secondary')}; 
                border-right: 1px solid {THEME.get_color('text_secondary')};
            }}
            QWidget#RightPanel {{
                background-color: transparent; 
            }}
            QWidget#InputContainer {{
                background-color: {THEME.get_color('background_secondary')};
                border-top: 1px solid {THEME.get_color('accent_dim')};
            }}
            QScrollBar:vertical {{
                border: none;
                background: {THEME.get_color('background')};
                width: {THEME.spacing['s']}px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {THEME.get_color('text_secondary')};
                min-height: {THEME.spacing['l']}px;
                border-radius: {THEME.spacing['xs']}px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {THEME.get_color('accent')};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QToolTip {{
                background-color: {THEME.get_color('background')};
                color: {THEME.get_color('accent')};
                border: 1px solid {THEME.get_color('accent')};
                font-family: "{THEME.fonts['family_main']}";
            }}
            QCheckBox {{
                color: {THEME.get_color('accent')};
                font-family: "{THEME.fonts['family_main']}";
                spacing: {THEME.spacing['s']}px;
            }}
            QCheckBox::indicator {{
                width: {THEME.spacing['m']}px;
                height: {THEME.spacing['m']}px;
                border: 1px solid {THEME.get_color('accent')};
                background: transparent;
            }}
            QCheckBox::indicator:checked {{
                background-color: {THEME.get_color('accent')};
            }}
        """)

    # ... [Keep rest of methods similar but update references] ...
    # To save space, I will implement the critical logic methods
    
    def add_system_message(self, text):
        lbl = QLabel(f">> SYSTEM: {text}")
        lbl.setStyleSheet(f"color: {THEME.get_color('accent')}; font-family: {THEME.fonts['family_code']}; margin: {THEME.spacing['xs']}px; font-size: {THEME.fonts['size_small']}px;")
        self.chat_layout.addWidget(lbl)
        self.scroll_to_bottom(force=False)
        if hasattr(self, 'log_viewer'):
            self.log_viewer.add_log("INFO", text)

    def add_chat_bubble(self, text, is_user):
        bubble = ChatBubble(text, is_user)
        self.chat_layout.addWidget(bubble)
        self.scroll_to_bottom(force=is_user)

    def scroll_to_bottom(self, force=False):
        scrollbar = self.scroll_area.verticalScrollBar()
        start = scrollbar.value()
        end = scrollbar.maximum()
        is_at_bottom = (end - start) <= 50
        
        if not force and not is_at_bottom:
            self.unread_count += 1
            self.update_scroll_button()
            return

        self.unread_count = 0
        self.update_scroll_button()
        
        def start_anim():
            end_val = scrollbar.maximum()
            if abs(end_val - start) < 5:
                scrollbar.setValue(end_val)
                return
            self.anim_scroll = QPropertyAnimation(scrollbar, b"value")
            self.anim_scroll.setDuration(300)
            self.anim_scroll.setStartValue(start)
            self.anim_scroll.setEndValue(end_val)
            self.anim_scroll.setEasingCurve(QEasingCurve.OutQuad)
            self.anim_scroll.start()
        
        QTimer.singleShot(50, start_anim)

    def on_scroll_value_changed(self, value):
        scrollbar = self.scroll_area.verticalScrollBar()
        if scrollbar.maximum() - value < 50:
            self.user_scrolled_up = False
            self.unread_count = 0
            self.update_scroll_button()
        else:
            self.user_scrolled_up = True
            self.update_scroll_button()

    def update_scroll_button(self):
        if not hasattr(self, 'btn_scroll_bottom'): return
        
        # Do not show scroll button if Multi-Agent Mode is active
        if hasattr(self, 'multi_agent_widget') and self.multi_agent_widget.isVisible():
            self.btn_scroll_bottom.hide()
            return

        if self.unread_count > 0:
            self.btn_scroll_bottom.setText(f"⇩ LATEST ({self.unread_count})")
            self.btn_scroll_bottom.setEnabled(True)
            self.btn_scroll_bottom.set_accent_color(THEME.get_color('accent_warn'))
        elif self.user_scrolled_up:
            self.btn_scroll_bottom.setText("⇩ LATEST")
            self.btn_scroll_bottom.setEnabled(True)
            self.btn_scroll_bottom.set_accent_color(None)
        else:
            self.btn_scroll_bottom.setText("● LATEST")
            self.btn_scroll_bottom.setEnabled(False)
            self.btn_scroll_bottom.set_accent_color(None)
        self.btn_scroll_bottom.show()
        self.btn_scroll_bottom.raise_()
        self.update_scroll_button_pos()

    def update_scroll_button_pos(self):
        if not hasattr(self, 'btn_scroll_bottom') or not self.btn_scroll_bottom.isVisible():
            return
        if not self.scroll_area.isVisible(): return
        geo = self.scroll_area.geometry()
        global_pos = self.scroll_area.mapToGlobal(geo.topLeft())
        local_pos = self.central_widget.mapFromGlobal(global_pos)
        x = local_pos.x() + (geo.width() - self.btn_scroll_bottom.width()) // 2
        y = local_pos.y() + geo.height() - self.btn_scroll_bottom.height() - 20
        self.btn_scroll_bottom.move(x, y)
        self.btn_scroll_bottom.raise_()

    def on_theme_updated(self):
        self.apply_styles()
        if hasattr(self, 'bg_particles'):
            self.bg_particles.update()
        self.add_system_message("Visual parameters synchronized with core.")

    def check_server(self):
        if self.check_worker and self.check_worker.isRunning():
            return
        self.check_worker = Worker(self.client.check_connection)
        self.check_worker.finished.connect(self.on_check_server_finished)
        self.check_worker.start()

    def on_check_server_finished(self, result):
        if result.get("data"):
            self.add_system_message("Uplink established. Core online.")
            self.status_server.set_status("online")
            self.fetch_voices()
            self.fetch_tts_preferences()
            QTimer.singleShot(100, self.theme_manager.fetch_theme)
        else:
            self.add_system_message("Uplink failed. Retrying sequence...")
            self.status_server.set_status("offline")
            QTimer.singleShot(3000, self.check_server)

    def fetch_tts_preferences(self):
        self.tts_pref_worker = Worker(self.client.get_profile)
        self.tts_pref_worker.finished.connect(self.on_tts_prefs_received)
        self.tts_pref_worker.start()

    def on_tts_prefs_received(self, result):
        prefs = result.get("data")
        if prefs and isinstance(prefs, dict):
            tts = prefs.get("tts_preferences", {}) if "tts_preferences" in prefs else prefs
            self.tts_speed = tts.get("speed", 100) / 100.0
            self.tts_volume = tts.get("volume", 100) / 100.0
            self.tts_voice = tts.get("voice_id", "default")
            self.add_system_message(f"TTS Config Synced: {self.tts_voice} @ {self.tts_speed}x")

    def fetch_voices(self):
        self.voice_worker = Worker(self.client.get_voices)
        self.voice_worker.finished.connect(self.on_voices_received)
        self.voice_worker.start()

    def on_voices_received(self, result):
        voices = result.get("data", {}) if isinstance(result, dict) and "data" in result else result
        if not voices or not isinstance(voices, dict):
            return
        self.available_voices = voices

    def update_tts_voice(self):
        pass

    def send_message(self, force_search=False):
        text = self.input_box.toPlainText().strip()
        if not text:
            return
        self.input_box.clear()
        if text.startswith("/"):
            self.handle_command(text)
            return
        self.add_chat_bubble(text, True)
        self.add_system_message("Processing request...")
        self.set_character_state("thinking")
        
        use_search = self.btn_search.isChecked() or force_search
        self.worker = Worker(self.client.send_message, text, use_search=use_search, force_search=force_search)
        self.worker.finished.connect(self.on_message_received)
        self.worker.start()

    def on_message_received(self, result):
        self.set_character_state("idle")
        if "error" in result:
            self.add_system_message(f"Error: {result['error']}")
            return
        data = result.get("data", {}) if "data" in result else result
        response = data.get("response", "")
        search_used = data.get("search_used", False)
        
        if search_used:
            self.add_system_message("Net Search Active: Data retrieved from external nodes.")
            
        self.add_chat_bubble(response, False)
        
        if self.btn_tts.isChecked():
            self.play_tts(response)

    def handle_command(self, text):
        cmd = text[1:].strip().lower()
        if cmd == "clear":
            self.clear_chat_visuals()
            self.add_system_message("Visual logs cleared.")
        elif cmd == "reset":
            self.clear_memory()
            self.clear_chat_visuals()
            self.add_system_message("System reset complete.")
        elif cmd == "help":
            help_text = "Commands: /clear, /reset, /help, /status"
            self.add_system_message(help_text)
        elif cmd == "status":
            self.update_server_status()
        else:
            self.add_system_message(f"Unknown command: {cmd}")

    def on_voice_text(self, text, is_final):
        if is_final:
            self.input_box.setPlainText(text)
            self.send_message()

    def on_wake_word(self):
        self.add_system_message("Wake Word Detected! Listening for command...")
        self.voice_system.set_mode("active")
        self.btn_voice.setText("ACTIVE")
        self.btn_voice.set_accent_color(THEME.get_color('accent_warn'))
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath("assets/sounds/wake.wav")))) # Optional
        self.player.play()

    def toggle_voice(self):
        if not hasattr(self, 'voice_widget_dialog'):
            self.voice_widget_dialog = QDialog(self)
            self.voice_widget_dialog.setWindowTitle("VOICE CONTROL")
            self.voice_widget_dialog.setWindowFlags(Qt.Tool)
            layout = QVBoxLayout(self.voice_widget_dialog)
            self.voice_ctrl = VoiceControlWidget()
            layout.addWidget(self.voice_ctrl)
            
            # Connect signals
            self.voice_ctrl.chk_vad.stateChanged.connect(self.update_vad_settings)
            self.voice_ctrl.chk_continuous.stateChanged.connect(self.toggle_continuous_mode)
            self.voice_ctrl.slider_thresh.valueChanged.connect(self.update_vad_settings)
            self.voice_system.level_changed.connect(self.voice_ctrl.visualizer.update_level)
            
        self.voice_widget_dialog.show()
        
        # Start/Stop
        if not self.voice_system.running:
            self.voice_system.start()
            self.btn_voice.setText("LISTENING")
            self.btn_voice.set_accent_color(THEME.get_color('accent_warn'))
        else:
            self.voice_system.stop()
            self.btn_voice.setText("VOICE")
            self.btn_voice.set_accent_color(None)

    def toggle_continuous_mode(self, state):
        self.continuous_mode = (state == Qt.Checked)
        mode = "continuous" if self.continuous_mode else "wake_word"
        self.voice_system.set_mode(mode)
        self.add_system_message(f"Voice Mode: {mode.upper()}")

    def update_vad_settings(self):
        if hasattr(self, 'voice_ctrl'):
            # self.voice_system.vad_threshold = self.voice_ctrl.slider_thresh.value() / 100.0
            pass # TODO: expose setting in VoiceSystem

    def on_silence_detected(self):
        pass # Managed by VoiceSystem internally via server commit

    def open_settings(self):
        dialog = SettingsDialog(self, self.client)
        if dialog.exec_():
            self.apply_settings()

    def show_multi_agent_mode(self):
        self.content_widget.hide()
        self.multi_agent_widget.show()
        if hasattr(self, 'btn_scroll_bottom'):
            self.btn_scroll_bottom.hide()
        self.add_system_message("Multi-Agent Collaboration Mode Initiated.")

    def hide_multi_agent_mode(self):
        self.multi_agent_widget.hide()
        self.content_widget.show()
        if hasattr(self, 'btn_scroll_bottom'):
            self.update_scroll_button()
        self.add_system_message("Returning to Standard Command Interface.")

    def toggle_chat_multi_mode(self):
        if self.multi_agent_widget.isVisible():
            self.hide_multi_agent_mode()
            self.btn_chat_multi.setText("CHAT-MULTI")
            self.btn_chat_multi.setStyleSheet(f"background: transparent; color: {THEME.get_color('accent')}; border: 1px solid {THEME.get_color('accent_dim')}; padding: 0 12px; border-radius: 16px;")
        else:
            self.show_multi_agent_mode()
            self.btn_chat_multi.setText("MULTI-ACTIVE")
            self.btn_chat_multi.setStyleSheet(f"background: {THEME.hex_to_rgba(THEME.get_color('accent'), 0.15)}; color: {THEME.get_color('accent')}; border: 1px solid {THEME.get_color('accent')}; padding: 0 12px; border-radius: 16px;")

    def apply_settings(self):
        res_text = self.settings.value("resolution", "1280x720 (HD)")
        self.apply_window_size(res_text)
        
        self.check_server()
        override = int(self.settings.value("ui_font_size_override", 0))
        if override > 0:
            self.set_ui_font_size(override)
        # speed = float(self.settings.value("animation_speed", 1.0))
        # THEME.set_animation_speed(speed)
        
        self.add_system_message("System configuration updated.")

    def manage_memory(self):
        self.add_system_message("Memory management interface accessed.")

    def clear_memory(self):
        self.worker_mem = Worker(self.client.clear_memory)
        self.worker_mem.finished.connect(lambda r: self.add_system_message("Memory purged."))
        self.worker_mem.start()

    def on_media_state_changed(self, state):
        if state == QMediaPlayer.StoppedState:
            pass

    def on_log_filter_changed(self, text):
        if hasattr(self, 'log_viewer'):
            self.log_viewer.set_filter(text)

    def on_user_typing(self):
        self.set_character_state("listening")

    def set_character_state(self, state):
        pass

    def update_local_status(self):
        try:
            import psutil
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            self.status_agent.set_status("online", f"CPU: {cpu}% MEM: {mem}%")
            if hasattr(self, 'radar'):
                self.radar.data = [
                    min(1.0, cpu/100.0), 
                    min(1.0, mem/100.0), 
                    0.5 + (cpu/200.0), 
                    0.7, 
                    0.6 
                ]
                self.radar.update()
        except:
            self.status_agent.set_status("online")

    def update_server_status(self):
        if self.status_worker and self.status_worker.isRunning():
            return
        self.status_worker = Worker(self.client.get_status)
        self.status_worker.finished.connect(self.on_status_received)
        self.status_worker.start()

    def on_status_received(self, result):
        data = result.get("data", {})
        import datetime
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.lbl_last_check.setText(f"SYNC: {now}")
        
        old_server_status = self.status_server.value_label.text()
        
        if "error" in result:
            new_status = "OFFLINE"
            if old_server_status != new_status:
                self.add_system_message(f"Status Change: UPLINK -> {new_status}")
                self.status_server.set_status("offline")
            self.status_llm.set_status("unknown")
            self.status_tts.set_status("unknown")
            return

        new_status = "ONLINE"
        if old_server_status != new_status:
            self.add_system_message(f"Status Change: UPLINK -> {new_status}")
            self.status_server.set_status("online")
        
        llm = data.get("llm", {})
        if llm.get("status"):
            self.status_llm.set_status("online", llm.get("message"))
        else:
            self.status_llm.set_status("offline", llm.get("message"))
            
        tts = data.get("tts", {})
        if tts.get("status"):
            self.status_tts.set_status("online", tts.get("message"))
        else:
            self.status_tts.set_status("offline", tts.get("message"))
            
    def change_avatar(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Avatar", "", "Images (*.png *.jpg)")
        if path:
            self.custom_avatar_path = path
            self.settings.setValue("avatar_path", path)
            self.load_avatar_image()

    def play_tts(self, text):
        self.tts_worker = Worker(self.client.get_tts, text, self.tts_speed, self.tts_volume, self.tts_voice)
        self.tts_worker.finished.connect(self.on_tts_audio_received)
        self.tts_worker.start()

    def on_tts_audio_received(self, result):
        data = result.get("data")
        if data:
            fd, path = tempfile.mkstemp(suffix=".wav")
            with os.fdopen(fd, 'wb') as f:
                f.write(data)
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
            self.player.play()

    def attach_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Attachment", "", "All Files (*)")
        if path:
            self.input_box.append(f"[ATTACHMENT: {os.path.basename(path)}]")

    def toggle_enter_behavior(self, state):
        self.input_box.set_send_on_enter(self.chk_enter_send.isChecked())

    def toggle_net_search(self, checked):
        if checked:
            self.btn_search.setText("NET: ON")
            self.btn_search.set_accent_color(THEME.get_color('success'))
        else:
            self.btn_search.setText("NET: OFF")
            self.btn_search.set_accent_color(None)

    def toggle_tts(self, checked):
        self.auto_tts_enabled = checked
        if checked:
            self.btn_tts.setText("TTS: ON")
            self.btn_tts.set_accent_color(THEME.get_color('success'))
        else:
            self.btn_tts.setText("TTS: OFF")
            self.btn_tts.set_accent_color(None)

    def clear_memory_confirm(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("CONFIRM PURGE")
        msg.setText("Are you sure you want to clear memory?")
        msg.setInformativeText("This action cannot be undone.")
        msg.setIcon(QMessageBox.Warning)
        btn_keep = msg.addButton("Clear Chat Only", QMessageBox.ActionRole)
        btn_all = msg.addButton("Clear All Memory", QMessageBox.ActionRole)
        btn_cancel = msg.addButton(QMessageBox.Cancel)
        msg.exec_()
        if msg.clickedButton() == btn_all:
            self.clear_memory()
            self.chat_layout.itemAt(0).widget().hide()
            self.clear_chat_visuals()
        elif msg.clickedButton() == btn_keep:
            self.clear_chat_visuals()
            self.add_system_message("Visual logs cleared. Memory retained.")

    def clear_chat_visuals(self):
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.chat_layout.addStretch()
