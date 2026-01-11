from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter, QTextEdit, QLineEdit, QComboBox, QTreeWidget, QTreeWidgetItem, QPlainTextEdit, QFileSystemModel, QTreeView)
from PyQt5.QtCore import Qt, pyqtSignal, QDir
from ..components import TacticalFrame, TacticalButton, ChatBubble
from ..framework.theme import THEME

class MultiAgentWidget(QWidget):
    close_requested = pyqtSignal()

    def __init__(self, parent=None, client=None):
        super().__init__(parent)
        self.client = client
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.projects_panel = TacticalFrame()
        self.chat_panel = TacticalFrame()
        self.viewer_panel = TacticalFrame()
        self.files_panel = TacticalFrame()
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.projects_panel)
        splitter.addWidget(self.chat_panel)
        splitter.addWidget(self.viewer_panel)
        splitter.addWidget(self.files_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 2)
        splitter.setStretchFactor(3, 1)
        self.layout.addWidget(splitter)
        self.setup_projects_panel()
        self.setup_chat_panel()
        self.setup_viewer_panel()
        self.setup_files_panel()
        self.project_id = ""
        self.refresh_projects_tree()
        
    def setup_projects_panel(self):
        layout = QVBoxLayout(self.projects_panel)
        layout.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        self.inp_project = QLineEdit()
        self.inp_project.setPlaceholderText("新建项目名称")
        self.btn_new_project = TacticalButton("新建项目")
        self.btn_new_project.clicked.connect(self.create_project)
        bar.addWidget(self.inp_project)
        bar.addWidget(self.btn_new_project)
        layout.addLayout(bar)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self.on_tree_clicked)
        layout.addWidget(self.tree)
        self.agent_bar = QHBoxLayout()
        self.inp_role = QLineEdit()
        self.inp_role.setPlaceholderText("智能体角色名")
        self.combo_model = QComboBox()
        self.combo_model.setEditable(True)
        self.btn_new_agent = TacticalButton("创建新智能体")
        self.btn_new_agent.clicked.connect(self.create_agent)
        self.agent_bar.addWidget(self.inp_role)
        self.agent_bar.addWidget(self.combo_model)
        self.agent_bar.addWidget(self.btn_new_agent)
        layout.addLayout(self.agent_bar)
        self.refresh_models_combo()
        
    def setup_chat_panel(self):
        layout = QVBoxLayout(self.chat_panel)
        bar = QHBoxLayout()
        lbl = QLabel("群聊")
        lbl.setStyleSheet(f"color: {THEME.get_color('accent')}; font-weight: bold; font-size: 16px;")
        self.btn_latest = TacticalButton("LATEST")
        self.btn_latest.set_accent_color(THEME.get_color('accent'))
        self.btn_latest.clicked.connect(self.scroll_chat_bottom)
        self.btn_back_chat = TacticalButton("返回聊天模式")
        self.btn_back_chat.clicked.connect(self.close_requested.emit)
        bar.addWidget(lbl)
        bar.addStretch()
        bar.addWidget(self.btn_latest)
        bar.addWidget(self.btn_back_chat)
        layout.addLayout(bar)
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet(f"QTextEdit {{ background-color: {THEME.hex_to_rgba(THEME.get_color('background_tertiary'), 0.5)}; color: {THEME.get_color('text_primary')}; border: 1px solid {THEME.get_color('border')}; font-family: {THEME.fonts['family_code']}; }}")
        layout.addWidget(self.chat_history)
        self.inp_chat = QLineEdit()
        self.inp_chat.setPlaceholderText("输入消息")
        self.btn_send_chat = TacticalButton("发送")
        self.btn_send_chat.clicked.connect(self.send_chat)
        h = QHBoxLayout()
        h.addWidget(self.inp_chat)
        h.addWidget(self.btn_send_chat)
        layout.addLayout(h)
    def scroll_chat_bottom(self):
        self.chat_history.moveCursor(self.chat_history.textCursor().End)
        
    def setup_viewer_panel(self):
        layout = QVBoxLayout(self.viewer_panel)
        lbl = QLabel("展示窗口")
        lbl.setStyleSheet(f"color: {THEME.get_color('accent')}; font-weight: bold; font-size: 16px;")
        layout.addWidget(lbl)
        self.viewer = QPlainTextEdit()
        self.viewer.setReadOnly(True)
        self.viewer.setStyleSheet(f"QPlainTextEdit {{ background-color: {THEME.get_color('background_tertiary')}; color: {THEME.get_color('text_primary')}; border: 1px solid {THEME.get_color('border')}; font-family: {THEME.fonts['family_code']}; }}")
        layout.addWidget(self.viewer)

    def setup_files_panel(self):
        layout = QVBoxLayout(self.files_panel)
        lbl = QLabel("文件管理器")
        lbl.setStyleSheet(f"color: {THEME.get_color('accent')}; font-weight: bold; font-size: 16px;")
        layout.addWidget(lbl)
        self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath(QDir.currentPath())
        self.fs_view = QTreeView()
        self.fs_view.setModel(self.fs_model)
        self.fs_view.setRootIndex(self.fs_model.index(QDir.currentPath()))
        layout.addWidget(self.fs_view)

    def create_project(self):
        name = self.inp_project.text().strip() or "新项目"
        result = self.client.create_project(name) if self.client else {}
        self.project_id = result.get("project_id", "")
        if self.project_id:
            self.refresh_projects_tree()
        else:
            pass

    def refresh_projects_tree(self):
        self.tree.clear()
        projects = self.client.list_projects().get("projects", []) if self.client else []
        for p in projects:
            p_item = QTreeWidgetItem([f"{p.get('name','')}"])
            p_item.setData(0, Qt.UserRole, ("project", p.get("id","")))
            self.tree.addTopLevelItem(p_item)
            grp = QTreeWidgetItem(["群聊"])
            grp.setData(0, Qt.UserRole, ("group", p.get("id","")))
            p_item.addChild(grp)
            agents = self.client.list_agents(p.get("id","")).get("agents", []) if self.client else []
            for a in agents:
                a_item = QTreeWidgetItem([f"{a.get('role_name','')}"])
                a_item.setData(0, Qt.UserRole, ("agent", p.get("id",""), a.get("role_name","")))
                p_item.addChild(a_item)
        self.tree.expandAll()

    def on_tree_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        t = data[0]
        if t == "project":
            self.project_id = data[1]
            self.refresh_group_log()
        elif t == "group":
            self.project_id = data[1]
            self.refresh_group_log()
        elif t == "agent":
            self.project_id = data[1]
            self.refresh_group_log()
    def refresh_models_combo(self):
        models = self.client.list_models().get("models", []) if self.client else []
        self.combo_model.clear()
        for m in models:
            text = f"{m.get('name','')} ({m.get('type','')})"
            self.combo_model.addItem(text, m.get("name",""))
    def create_agent(self):
        if not self.project_id:
            return
        role = self.inp_role.text().strip() or "执行助手"
        model = self.combo_model.currentData() or "server-qwen2.5-7b"
        desc = ""
        r = self.client.create_agent(self.project_id, role, model, desc)
        if r.get("ok"):
            self.refresh_projects_tree()

    def send_chat(self):
        if not self.project_id:
            return
        text = self.inp_chat.text().strip()
        if not text:
            return
        r = self.client.orchestrate(self.project_id, text) if self.client else {}
        self.inp_chat.clear()
        self.refresh_group_log()

    def refresh_group_log(self):
        if not self.project_id:
            return
        log = self.client.get_project_log(self.project_id).get("log", []) if self.client else []
        self.chat_history.clear()
        for o in log:
            line = f"[{o.get('timestamp','')}] {o.get('role','')} {o.get('model','')}: {o.get('content','')}"
            self.chat_history.append(line)
        if log:
            last = log[-1]
            self.viewer.setPlainText(last.get("content",""))
