from PyQt5.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QCheckBox, QComboBox, QTabWidget, 
                             QFormLayout, QScrollArea, QFrame, QSpinBox, QDoubleSpinBox,
                             QMessageBox, QListWidget, QListWidgetItem, QStackedWidget, QFileDialog, QStackedLayout)
from PyQt5.QtCore import Qt, QSettings, pyqtSignal
from PyQt5.QtGui import QColor
from ..framework.theme import THEME
from ..components import TacticalButton, TacticalFrame, ParticleBackground
from ..api_client import APIClient
import json
import os

class SettingsDialog(QDialog):
    def __init__(self, parent=None, client=None):
        super().__init__(parent)
        self.client = client
        self.settings = QSettings("Eliza", "Client")
        self.setWindowTitle("SYSTEM CONFIGURATION")
        self.resize(800, 600)
        self.initial_settings = {}
        self.changed_settings = {}
        
        # Apply Theme
        self.setStyleSheet(THEME.get_qss())
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        # Use Stacked Layout to support Particle Background
        self.main_stack = QStackedLayout(self)
        self.main_stack.setStackingMode(QStackedLayout.StackAll)
        
        # Background
        assets_dir = os.path.join(os.path.dirname(__file__), "../assets")
        griffin_path = os.path.join(assets_dir, "griffin_logo.png")
        sf_path = os.path.join(assets_dir, "sf_logo.jpg")
        
        self.bg_particles = ParticleBackground(parent=self, griffin_logo=griffin_path, sf_logo=sf_path)
        self.main_stack.addWidget(self.bg_particles)
        
        # Content Container
        self.content_container = QWidget()
        self.content_container.setAttribute(Qt.WA_TranslucentBackground)
        self.main_stack.addWidget(self.content_container)
        self.content_container.raise_()
        
        self.layout = QVBoxLayout(self.content_container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet(f"background-color: {THEME.get_color('background_secondary')}; border-bottom: 1px solid {THEME.get_color('accent_dim')};")
        header_layout = QHBoxLayout(header)
        
        title = QLabel("SYSTEM CONFIGURATION // ADVANCED")
        title.setStyleSheet(f"color: {THEME.get_color('accent')}; font-size: 16px; font-weight: bold; letter-spacing: 2px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("SEARCH CONFIG...")
        self.search_bar.setFixedWidth(250)
        self.search_bar.textChanged.connect(self.filter_settings)
        header_layout.addWidget(self.search_bar)
        
        self.layout.addWidget(header)
        
        # Content
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet(f"""
            QListWidget {{
                background-color: {THEME.get_color('background_secondary')};
                border: none;
                border-right: 1px solid {THEME.get_color('border')};
            }}
            QListWidget::item {{
                padding: 15px;
                color: {THEME.get_color('text_secondary')};
                font-weight: bold;
            }}
            QListWidget::item:selected {{
                background-color: {THEME.hex_to_rgba(THEME.get_color('accent'), 0.1)};
                color: {THEME.get_color('accent')};
                border-left: 3px solid {THEME.get_color('accent')};
            }}
        """)
        self.sidebar.currentRowChanged.connect(self.change_page)
        content_layout.addWidget(self.sidebar)
        
        # Pages
        self.pages = QStackedWidget()
        self.pages.setAttribute(Qt.WA_TranslucentBackground)
        content_layout.addWidget(self.pages)
        
        self.layout.addWidget(content)
        
        # Footer
        footer = QFrame()
        footer.setFixedHeight(60)
        footer.setStyleSheet(f"background-color: {THEME.get_color('background_secondary')}; border-top: 1px solid {THEME.get_color('accent_dim')};")
        footer_layout = QHBoxLayout(footer)
        
        btn_reset = TacticalButton("RESET DEFAULT", parent=self)
        btn_reset.setFixedSize(150, 36)
        btn_reset.set_accent_color(THEME.get_color('warning'))
        btn_reset.clicked.connect(self.reset_defaults)
        
        footer_layout.addWidget(btn_reset)
        footer_layout.addStretch()
        
        btn_cancel = TacticalButton("CANCEL", parent=self)
        btn_cancel.setFixedSize(100, 36)
        btn_cancel.set_accent_color(THEME.get_color('text_secondary'))
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = TacticalButton("APPLY CHANGES", parent=self)
        btn_save.setFixedSize(150, 36)
        btn_save.clicked.connect(self.save_settings)
        
        footer_layout.addWidget(btn_cancel)
        footer_layout.addWidget(btn_save)
        
        self.layout.addWidget(footer)
        
        # Initialize Pages
        self.init_general_page()
        self.init_network_page()
        self.init_appearance_page()
        self.init_audio_page()
        self.init_memory_page()
        self.init_advanced_page()
        
        self.sidebar.setCurrentRow(0)

    def add_page(self, name, widget):
        item = QListWidgetItem(name)
        self.sidebar.addItem(item)
        self.pages.addWidget(widget)

    def change_page(self, index):
        self.pages.setCurrentIndex(index)

    def create_form_page(self):
        page = QWidget()
        page.setAttribute(Qt.WA_TranslucentBackground)
        scroll = QScrollArea(page)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        content = QWidget()
        content.setAttribute(Qt.WA_TranslucentBackground)
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        return page, layout

    def add_section(self, layout, title):
        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {THEME.get_color('accent')}; font-size: 14px; font-weight: bold; border-bottom: 1px solid {THEME.get_color('accent_dim')}; padding-bottom: 5px; margin-top: 10px;")
        layout.addWidget(lbl)

    def add_setting(self, layout, label, widget, key, default):
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel(label)
        lbl.setFixedWidth(200)
        
        h_layout.addWidget(lbl)
        h_layout.addWidget(widget)
        
        layout.addWidget(container)
        
        # Store widget ref for saving/loading
        if not hasattr(self, 'setting_widgets'):
            self.setting_widgets = {}
        self.setting_widgets[key] = {'widget': widget, 'default': default}

    def init_general_page(self):
        page, layout = self.create_form_page()
        
        self.add_section(layout, "System Preferences")
        
        chk_autorun = QCheckBox("Auto-Connect on Startup")
        self.add_setting(layout, "Startup:", chk_autorun, "general/auto_connect", False)
        
        chk_notifications = QCheckBox("Enable Desktop Notifications")
        self.add_setting(layout, "Notifications:", chk_notifications, "general/notifications", True)
        
        chk_check_updates = QCheckBox("Check for Updates Automatically")
        self.add_setting(layout, "Updates:", chk_check_updates, "general/check_updates", True)

        self.add_section(layout, "Memory")
        
        spin_history = QSpinBox()
        spin_history.setRange(10, 500)
        spin_history.setValue(50)
        self.add_setting(layout, "Max Chat History:", spin_history, "general/max_history", 50)
        
        layout.addStretch()
        self.add_page("GENERAL", page)

    def init_network_page(self):
        page, layout = self.create_form_page()
        
        self.add_section(layout, "Connection")
        
        inp_url = QLineEdit()
        inp_url.setPlaceholderText("http://localhost:8000")
        self.add_setting(layout, "Server URL:", inp_url, "server_url", "http://localhost:8000")
        
        spin_timeout = QSpinBox()
        spin_timeout.setRange(1, 60)
        spin_timeout.setSuffix("s")
        self.add_setting(layout, "Request Timeout:", spin_timeout, "network/timeout", 30)
        
        self.add_section(layout, "API Keys")
        
        inp_openai = QLineEdit()
        inp_openai.setEchoMode(QLineEdit.Password)
        self.add_setting(layout, "OpenAI Key:", inp_openai, "keys/openai", "")
        
        layout.addStretch()
        self.add_page("NETWORK", page)

    def init_appearance_page(self):
        page, layout = self.create_form_page()
        
        self.add_section(layout, "Display")
        
        combo_res = QComboBox()
        combo_res.addItems(["1280x720 (HD)", "1920x1080 (FHD)", "1366x768", "1024x768", "800x600", "Fullscreen"])
        self.add_setting(layout, "Window Size:", combo_res, "resolution", "1280x720 (HD)")

        spin_font = QSpinBox()
        spin_font.setRange(0, 24)
        spin_font.setToolTip("0 = Auto")
        self.add_setting(layout, "Font Size Override:", spin_font, "ui_font_size_override", 0)

        chk_particles = QCheckBox("Enable Particle Effects")
        self.add_setting(layout, "Visual Effects:", chk_particles, "visuals/particles", True)
        
        spin_opacity = QSpinBox()
        spin_opacity.setRange(50, 100)
        spin_opacity.setSuffix("%")
        self.add_setting(layout, "Window Opacity:", spin_opacity, "visuals/opacity", 100)

        speed = QDoubleSpinBox()
        speed.setRange(0.5, 2.0)
        speed.setSingleStep(0.1)
        self.add_setting(layout, "Animation Speed:", speed, "animation_speed", 1.0)
        
        layout.addStretch()
        self.add_page("APPEARANCE", page)

    def init_audio_page(self):
        page, layout = self.create_form_page()
        
        self.add_section(layout, "Text-to-Speech")
        
        slider_vol = QDoubleSpinBox()
        slider_vol.setRange(0.0, 1.0)
        slider_vol.setSingleStep(0.1)
        self.add_setting(layout, "Volume:", slider_vol, "tts_volume", 1.0)
        
        slider_speed = QDoubleSpinBox()
        slider_speed.setRange(0.5, 2.0)
        slider_speed.setSingleStep(0.1)
        self.add_setting(layout, "Speed:", slider_speed, "tts_speed", 1.0)
        
        combo_voice = QComboBox()
        # This would ideally be populated dynamically
        combo_voice.addItems(["default", "alloy", "echo", "fable", "onyx", "nova", "shimmer"])
        self.add_setting(layout, "Voice ID:", combo_voice, "tts_voice", "default")
        
        self.add_section(layout, "Microphone")
        
        chk_vad = QCheckBox("Enable Voice Activity Detection")
        self.add_setting(layout, "VAD:", chk_vad, "audio/vad_enabled", True)
        
        layout.addStretch()
        self.add_page("AUDIO", page)

    def init_memory_page(self):
        page, layout = self.create_form_page()
        self.add_section(layout, "Memory System")

        decay = QDoubleSpinBox()
        decay.setRange(0.001, 0.2)
        decay.setSingleStep(0.001)
        self.add_setting(layout, "Decay Rate:", decay, "preferences.memory_decay_rate", 0.05)

        stm = QSpinBox()
        stm.setRange(5, 100)
        self.add_setting(layout, "STM Capacity:", stm, "preferences.stm_capacity", 10)

        primacy = QDoubleSpinBox()
        primacy.setRange(0.0, 1.0)
        primacy.setSingleStep(0.05)
        self.add_setting(layout, "Primacy Weight:", primacy, "preferences.primacy_weight", 0.2)

        recency = QDoubleSpinBox()
        recency.setRange(0.0, 1.0)
        recency.setSingleStep(0.05)
        self.add_setting(layout, "Recency Weight:", recency, "preferences.recency_weight", 0.3)

        semantic = QDoubleSpinBox()
        semantic.setRange(0.0, 1.0)
        semantic.setSingleStep(0.05)
        self.add_setting(layout, "Semantic Weight:", semantic, "preferences.semantic_weight", 0.6)

        emotion = QDoubleSpinBox()
        emotion.setRange(0.0, 1.0)
        emotion.setSingleStep(0.05)
        self.add_setting(layout, "Emotion Weight:", emotion, "preferences.emotion_weight", 0.2)

        layout.addStretch()
        self.add_page("MEMORY", page)

    def init_advanced_page(self):
        page, layout = self.create_form_page()
        self.add_section(layout, "Theme")

        depth = QDoubleSpinBox()
        depth.setRange(0.8, 1.2)
        depth.setSingleStep(0.05)
        self.add_setting(layout, "Theme Depth:", depth, "appearance/theme_depth", 1.0)

        antialias = QCheckBox("Font Antialiasing")
        self.add_setting(layout, "Rendering:", antialias, "appearance/font_antialias", True)

        self.add_section(layout, "Config Sync")

        btn_export = TacticalButton("EXPORT CONFIG", parent=self)
        btn_import = TacticalButton("IMPORT CONFIG", parent=self)
        btn_export.clicked.connect(self.export_profile)
        btn_import.clicked.connect(self.import_profile)
        container = QWidget()
        hl = QHBoxLayout(container)
        hl.addWidget(btn_export)
        hl.addWidget(btn_import)
        layout.addWidget(container)

        layout.addStretch()
        self.add_page("ADVANCED", page)

    def load_settings(self):
        for key, data in self.setting_widgets.items():
            widget = data['widget']
            default = data['default']
            
            val = self.settings.value(key, default)
            
            # Type conversion
            if isinstance(default, bool):
                val = str(val).lower() == 'true'
            elif isinstance(default, int):
                val = int(val)
            elif isinstance(default, float):
                val = float(val)
                
            # Set widget value
            if isinstance(widget, QCheckBox):
                widget.setChecked(val)
            elif isinstance(widget, QLineEdit):
                widget.setText(str(val))
            elif isinstance(widget, QComboBox):
                index = widget.findText(str(val))
                if index >= 0:
                    widget.setCurrentIndex(index)
                else:
                    # If value not in list, add it or set default
                    widget.addItem(str(val))
                    widget.setCurrentText(str(val))
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(val)
                
            self.initial_settings[key] = val

    def save_settings(self):
        profile_updates = {}
        for key, data in self.setting_widgets.items():
            widget = data['widget']
            val = None
            
            if isinstance(widget, QCheckBox):
                val = widget.isChecked()
            elif isinstance(widget, QLineEdit):
                val = widget.text()
            elif isinstance(widget, QComboBox):
                val = widget.currentText()
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                val = widget.value()
                
            self.settings.setValue(key, val)
            
            # Update client if needed
            if key == "server_url" and self.client:
                self.client.base_url = val
            if key.startswith("preferences.") and self.client:
                profile_updates[key] = val

        if profile_updates and self.client:
            try:
                self.client.update_profile(profile_updates)
            except Exception:
                pass
        
        self.accept()
        QMessageBox.information(self, "Settings", "Configuration saved successfully.")

    def reset_defaults(self):
        reply = QMessageBox.question(self, "Reset Defaults", "Are you sure you want to reset all settings to default?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            for key, data in self.setting_widgets.items():
                widget = data['widget']
                default = data['default']
                
                if isinstance(widget, QCheckBox):
                    widget.setChecked(default)
                elif isinstance(widget, QLineEdit):
                    widget.setText(str(default))
                elif isinstance(widget, QComboBox):
                    index = widget.findText(str(default))
                    if index >= 0: widget.setCurrentIndex(index)
                elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                    widget.setValue(default)

    def filter_settings(self, text):
        text = text.lower()
        # Placeholder for filter logic
        pass

    def export_profile(self):
        if not self.client:
            return
        try:
            data = self.client.export_profile()
            if data:
                filename, _ = QFileDialog.getSaveFileName(self, "Export Settings", "", "JSON Files (*.json)")
                if filename:
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(data)
        except Exception:
            pass

    def import_profile(self):
        if not self.client:
            return
        filename, _ = QFileDialog.getOpenFileName(self, "Import Settings", "", "JSON Files (*.json)")
        if not filename:
            return
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.client.import_profile(data)
            QMessageBox.information(self, "Import", "Settings imported.")
        except Exception:
            QMessageBox.warning(self, "Import", "Failed to import settings.")
