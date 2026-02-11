from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSlider, QCheckBox, QGroupBox, QComboBox)
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from ..framework.theme import THEME
from ..framework.i18n import I18N

class WaveformVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(60)
        self.level = 0.0
        self.history = [0.0] * 50
        self.setStyleSheet(f"background-color: {THEME.get_color('background')}; border: 1px solid {THEME.get_color('text_secondary')};")
        
    def update_level(self, level):
        self.level = level
        self.history.append(level)
        self.history.pop(0)
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(THEME.get_color('background')))
        
        # Draw Waveform
        width = self.width()
        height = self.height()
        bar_width = width / len(self.history)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(THEME.get_color('accent')))
        
        for i, val in enumerate(self.history):
            h = min(height, val * height * 10) 
            x = i * bar_width
            y = (height - h) / 2
            
            painter.drawRect(int(x), int(y), int(bar_width) - 1, int(h))

class VoiceControlWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(THEME.get_qss())
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)

        # Connect language change signal
        I18N.language_changed.connect(self.retranslate_ui)
        
        self.slider_style = f"""
            QSlider::groove:horizontal {{
                border: 1px solid {THEME.get_color('text_secondary')};
                height: 4px;
                background: {THEME.hex_to_rgba(THEME.get_color('background'), 0.5)};
                margin: 2px 0;
            }}
            QSlider::handle:horizontal {{
                background: {THEME.get_color('accent')};
                border: 1px solid {THEME.get_color('accent')};
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 0px;
            }}
            QSlider::sub-page:horizontal {{
                background: {THEME.hex_to_rgba(THEME.get_color('accent'), 0.5)};
                height: 4px;
            }}
        """
        
        self.combo_style = f"""
            QComboBox {{
                background: {THEME.hex_to_rgba(THEME.get_color('background'), 0.8)};
                color: {THEME.get_color('accent')};
                border: 1px solid {THEME.get_color('text_secondary')};
                padding: 5px;
                font-family: "{THEME.fonts['family_main']}";
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: {THEME.get_color('text_secondary')};
                border-left-style: solid;
            }}
            QComboBox QAbstractItemView {{
                background: {THEME.get_color('background')};
                color: {THEME.get_color('text_primary')};
                selection-background-color: {THEME.get_color('accent')};
                selection-color: #000000;
                border: 1px solid {THEME.get_color('accent')};
            }}
        """
        
        # --- ASR / VAD Section ---
        self.group_vad = QGroupBox(I18N.t("voice_group_vad"))
        self.group_vad.setStyleSheet(f"""
            QGroupBox {{ 
                color: {THEME.get_color('accent')}; 
                font-weight: bold; 
                border: 1px solid {THEME.get_color('text_secondary')}; 
                margin-top: 10px; 
            }} 
            QGroupBox::title {{ 
                subcontrol-origin: margin; 
                left: 10px; 
                padding: 0 3px; 
            }}
        """)
        vad_layout = QVBoxLayout(self.group_vad)
        
        # Visualizer
        self.visualizer = WaveformVisualizer()
        vad_layout.addWidget(self.visualizer)
        
        # VAD Toggle
        self.chk_vad = QCheckBox(I18N.t("voice_chk_vad"))
        self.chk_vad.setStyleSheet(f"color: {THEME.get_color('text_primary')};")
        vad_layout.addWidget(self.chk_vad)

        # Continuous Mode Toggle
        self.chk_continuous = QCheckBox(I18N.t("voice_chk_continuous"))
        self.chk_continuous.setStyleSheet(f"color: {THEME.get_color('text_primary')};")
        vad_layout.addWidget(self.chk_continuous)
        
        # Threshold Slider
        thresh_layout = QHBoxLayout()
        self.lbl_thresh = QLabel(f"{I18N.t('voice_lbl_threshold')} 0.01")
        self.lbl_thresh.setStyleSheet(f"color: {THEME.get_color('text_primary')};")
        thresh_layout.addWidget(self.lbl_thresh)
        
        self.slider_thresh = QSlider(Qt.Horizontal)
        self.slider_thresh.setRange(1, 50) # 0.01 to 0.50
        self.slider_thresh.setValue(1)
        self.slider_thresh.setStyleSheet(self.slider_style)
        self.slider_thresh.valueChanged.connect(self.update_thresh_label)
        thresh_layout.addWidget(self.slider_thresh)
        vad_layout.addLayout(thresh_layout)
        
        self.layout.addWidget(self.group_vad)
        
        # --- TTS Section ---
        self.group_tts = QGroupBox(I18N.t("voice_group_tts"))
        self.group_tts.setStyleSheet(f"""
            QGroupBox {{ 
                color: {THEME.get_color('accent')}; 
                font-weight: bold; 
                border: 1px solid {THEME.get_color('text_secondary')}; 
                margin-top: 10px; 
            }} 
            QGroupBox::title {{ 
                subcontrol-origin: margin; 
                left: 10px; 
                padding: 0 3px; 
            }}
        """)
        tts_layout = QVBoxLayout(self.group_tts)
        
        # Voice Selection
        voice_layout = QHBoxLayout()
        self.lbl_voice_label = QLabel(I18N.t("voice_lbl_voice"))
        self.lbl_voice_label.setStyleSheet(f"color: {THEME.get_color('text_primary')};")
        voice_layout.addWidget(self.lbl_voice_label)
        
        self.combo_voice = QComboBox()
        self.combo_voice.setStyleSheet(self.combo_style)
        voice_layout.addWidget(self.combo_voice)
        tts_layout.addLayout(voice_layout)

        # Speed
        speed_layout = QHBoxLayout()
        self.lbl_speed = QLabel(f"{I18N.t('voice_lbl_speed')} 1.0x")
        self.lbl_speed.setStyleSheet(f"color: {THEME.get_color('text_primary')};")
        speed_layout.addWidget(self.lbl_speed)
        
        self.slider_speed = QSlider(Qt.Horizontal)
        self.slider_speed.setRange(5, 20) # 0.5 to 2.0
        self.slider_speed.setValue(10)
        self.slider_speed.setStyleSheet(self.slider_style)
        self.slider_speed.valueChanged.connect(self.update_speed_label)
        speed_layout.addWidget(self.slider_speed)
        tts_layout.addLayout(speed_layout)
        
        # Volume
        vol_layout = QHBoxLayout()
        self.lbl_vol = QLabel(f"{I18N.t('voice_lbl_volume')} 1.0x")
        self.lbl_vol.setStyleSheet(f"color: {THEME.get_color('text_primary')};")
        vol_layout.addWidget(self.lbl_vol)
        
        self.slider_vol = QSlider(Qt.Horizontal)
        self.slider_vol.setRange(0, 20) # 0.0 to 2.0
        self.slider_vol.setValue(10)
        self.slider_vol.setStyleSheet(self.slider_style)
        self.slider_vol.valueChanged.connect(self.update_vol_label)
        vol_layout.addWidget(self.slider_vol)
        tts_layout.addLayout(vol_layout)
        
        self.layout.addWidget(self.group_tts)
        
        self.layout.addStretch()

    def update_thresh_label(self, val):
        self.lbl_thresh.setText(f"{I18N.t('voice_lbl_threshold')} {val/100:.2f}")

    def update_speed_label(self, val):
        self.lbl_speed.setText(f"{I18N.t('voice_lbl_speed')} {val/10:.1f}x")

    def update_vol_label(self, val):
        self.lbl_vol.setText(f"{I18N.t('voice_lbl_volume')} {val/10:.1f}x")

    def retranslate_ui(self):
        self.group_vad.setTitle(I18N.t("voice_group_vad"))
        self.chk_vad.setText(I18N.t("voice_chk_vad"))
        self.chk_continuous.setText(I18N.t("voice_chk_continuous"))
        self.group_tts.setTitle(I18N.t("voice_group_tts"))
        if hasattr(self, 'lbl_voice_label'):
            self.lbl_voice_label.setText(I18N.t("voice_lbl_voice"))
        
        # Update labels with current values
        self.update_thresh_label(self.slider_thresh.value())
        self.update_speed_label(self.slider_speed.value())
        self.update_vol_label(self.slider_vol.value())
