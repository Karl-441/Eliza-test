from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QLabel, QSplitter, QTextEdit, QFrame, QLineEdit, QComboBox, QListWidgetItem, QTabWidget, QFormLayout, QCheckBox, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal
from ..components import TacticalFrame, TacticalButton, ChatBubble
from ..framework.theme import THEME

class MultiAgentWidget(QWidget):
    close_requested = pyqtSignal()

    def __init__(self, parent=None, client=None):
        super().__init__(parent)
        self.client = client
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Left: Configuration
        self.config_panel = TacticalFrame()
        self.setup_config_panel()
        
        # Center: Discussion
        self.discussion_panel = TacticalFrame()
        self.setup_discussion_panel()
        
        # Right: Controls
        self.control_panel = TacticalFrame()
        self.setup_control_panel()
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.config_panel)
        splitter.addWidget(self.discussion_panel)
        splitter.addWidget(self.control_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 1)
        
        self.layout.addWidget(splitter)
        
    def setup_config_panel(self):
        layout = QVBoxLayout(self.config_panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; }}
            QTabBar::tab {{
                background: {THEME.get_color('background_secondary')};
                color: {THEME.get_color('text_secondary')};
                padding: 8px 12px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {THEME.get_color('background_tertiary')};
                color: {THEME.get_color('accent')};
                border-bottom: 2px solid {THEME.get_color('accent')};
            }}
        """)
        
        # Tab 1: Roster
        roster_tab = QWidget()
        roster_layout = QVBoxLayout(roster_tab)
        
        self.agent_list = QListWidget()
        self.agent_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {THEME.get_color('background_secondary')};
                border: 1px solid {THEME.get_color('border')};
                color: {THEME.get_color('text_primary')};
            }}
            QListWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {THEME.get_color('accent_dim')};
            }}
            QListWidget::item:selected {{
                background-color: {THEME.hex_to_rgba(THEME.get_color('accent'), 0.1)};
                border-left: 2px solid {THEME.get_color('accent')};
            }}
        """)
        
        self.agents = [
            {"name": "Coordinator", "role": "System", "model": "gpt-4"},
            {"name": "Analyst", "role": "Text Analysis", "model": "gpt-3.5"},
            {"name": "Visualizer", "role": "Image Gen", "model": "dall-e"}
        ]
        
        for agent in self.agents:
            item = QListWidgetItem(f"{agent['name']} [{agent['role']}]")
            self.agent_list.addItem(item)
            
        roster_layout.addWidget(self.agent_list)
        btn_add = TacticalButton("DEPLOY NEW AGENT")
        roster_layout.addWidget(btn_add)
        
        self.tabs.addTab(roster_tab, "ROSTER")
        
        # Tab 2: Identity
        identity_tab = QWidget()
        id_layout = QFormLayout(identity_tab)
        id_layout.setSpacing(15)
        
        self.inp_name = QLineEdit()
        self.inp_name.setStyleSheet(f"background: {THEME.get_color('background_tertiary')}; color: {THEME.get_color('text_primary')}; border: 1px solid {THEME.get_color('border')}; padding: 5px;")
        
        self.combo_role = QComboBox()
        self.combo_role.addItems(["System", "User", "Assistant", "Critic", "Executor"])
        self.combo_role.setStyleSheet(f"background: {THEME.get_color('background_tertiary')}; color: {THEME.get_color('text_primary')}; border: 1px solid {THEME.get_color('border')}; padding: 5px;")
        
        self.combo_model = QComboBox()
        self.combo_model.addItems(["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "local-llama-3", "server-qwen2.5"]) # Mocked
        self.combo_model.setStyleSheet(f"background: {THEME.get_color('background_tertiary')}; color: {THEME.get_color('text_primary')}; border: 1px solid {THEME.get_color('border')}; padding: 5px;")
        
        self.combo_perms = QComboBox()
        self.combo_perms.addItems(["Read Only", "Read/Write", "Admin", "Execute Code"])
        self.combo_perms.setStyleSheet(f"background: {THEME.get_color('background_tertiary')}; color: {THEME.get_color('text_primary')}; border: 1px solid {THEME.get_color('border')}; padding: 5px;")
        
        id_layout.addRow(QLabel("Name:", styleSheet=f"color: {THEME.get_color('text_secondary')};"), self.inp_name)
        id_layout.addRow(QLabel("Role:", styleSheet=f"color: {THEME.get_color('text_secondary')};"), self.combo_role)
        id_layout.addRow(QLabel("Model:", styleSheet=f"color: {THEME.get_color('text_secondary')};"), self.combo_model)
        id_layout.addRow(QLabel("Access:", styleSheet=f"color: {THEME.get_color('text_secondary')};"), self.combo_perms)
        
        btn_save_id = TacticalButton("UPDATE IDENTITY")
        id_layout.addWidget(btn_save_id)
        
        self.tabs.addTab(identity_tab, "IDENTITY")
        
        # Tab 3: Team
        team_tab = QWidget()
        team_layout = QVBoxLayout(team_tab)
        
        grp_invite = QGroupBox("Invite Member")
        grp_invite.setStyleSheet(f"QGroupBox {{ color: {THEME.get_color('accent')}; border: 1px solid {THEME.get_color('accent_dim')}; margin-top: 10px; }} QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 3px; }}")
        invite_layout = QVBoxLayout(grp_invite)
        
        inp_invite = QLineEdit()
        inp_invite.setPlaceholderText("Enter User ID / Email")
        inp_invite.setStyleSheet(f"background: {THEME.get_color('background_tertiary')}; color: {THEME.get_color('text_primary')}; border: 1px solid {THEME.get_color('border')}; padding: 5px;")
        
        btn_invite = TacticalButton("SEND INVITE")
        invite_layout.addWidget(inp_invite)
        invite_layout.addWidget(btn_invite)
        
        team_layout.addWidget(grp_invite)
        
        grp_perms = QGroupBox("Team Permissions")
        grp_perms.setStyleSheet(f"QGroupBox {{ color: {THEME.get_color('accent')}; border: 1px solid {THEME.get_color('accent_dim')}; margin-top: 10px; }}")
        perms_layout = QVBoxLayout(grp_perms)
        
        chk_shared_mem = QCheckBox("Shared Memory Access")
        chk_shared_mem.setStyleSheet(f"color: {THEME.get_color('text_primary')};")
        chk_auto_exec = QCheckBox("Auto-Execution")
        chk_auto_exec.setStyleSheet(f"color: {THEME.get_color('text_primary')};")
        
        perms_layout.addWidget(chk_shared_mem)
        perms_layout.addWidget(chk_auto_exec)
        
        team_layout.addWidget(grp_perms)
        team_layout.addStretch()
        
        self.tabs.addTab(team_tab, "TEAM")
        
        layout.addWidget(self.tabs)
        
    def setup_discussion_panel(self):
        layout = QVBoxLayout(self.discussion_panel)
        lbl = QLabel("NEURAL SYNC STREAM")
        lbl.setStyleSheet(f"color: {THEME.get_color('accent')}; font-weight: bold; font-size: 16px;")
        layout.addWidget(lbl)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: {THEME.hex_to_rgba(THEME.get_color('background_tertiary'), 0.5)};
                color: {THEME.get_color('text_primary')};
                border: 1px solid {THEME.get_color('border')};
                font-family: {THEME.fonts['family_code']};
            }}
        """)
        layout.addWidget(self.chat_display)
        
    def setup_control_panel(self):
        layout = QVBoxLayout(self.control_panel)
        lbl = QLabel("SYNC CONTROL")
        lbl.setStyleSheet(f"color: {THEME.get_color('accent')}; font-weight: bold; font-size: 16px;")
        layout.addWidget(lbl)
        
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("Set Discussion Topic...")
        self.topic_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME.get_color('background_tertiary')};
                color: {THEME.get_color('text_primary')};
                border: 1px solid {THEME.get_color('border')};
                padding: 8px;
            }}
        """)
        layout.addWidget(self.topic_input)
        
        btn_start = TacticalButton("INITIATE SEQUENCE")
        btn_start.set_accent_color(THEME.get_color('success'))
        layout.addWidget(btn_start)
        
        layout.addStretch()
        
        self.status_lbl = QLabel("STATUS: IDLE")
        self.status_lbl.setStyleSheet(f"color: {THEME.get_color('text_secondary')}; font-weight: bold;")
        layout.addWidget(self.status_lbl)
        
        btn_export = TacticalButton("EXPORT LOGS")
        layout.addWidget(btn_export)
        
        btn_back = TacticalButton("RETURN TO DASHBOARD")
        btn_back.set_accent_color(THEME.get_color('text_secondary'))
        btn_back.clicked.connect(self.close_requested.emit)
        layout.addWidget(btn_back)
