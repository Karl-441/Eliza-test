from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter, QTextEdit, QLineEdit, QComboBox, QTreeWidget, QTreeWidgetItem, QPlainTextEdit, QFileSystemModel, QTreeView, QListWidget, QListWidgetItem, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QDir
from ..components import TacticalFrame, TacticalButton, ChatBubble
from ..framework.theme import THEME
from ..framework.websocket import WebSocketClient
import uuid
import webbrowser

class MultiAgentWidget(QWidget):
    close_requested = pyqtSignal()

    def __init__(self, parent=None, client=None):
        super().__init__(parent)
        self.client = client
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # WebSocket Setup
        self.client_id = str(uuid.uuid4())
        # Assuming server is localhost:8000. In prod, get from config.
        self.ws_client = WebSocketClient(f"ws://localhost:8000/api/v1/dashboard/ws/{self.client_id}")
        self.ws_client.message_received.connect(self.on_ws_message)
        self.ws_client.start()
        
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
        
        # Template Selection
        self.combo_template = QComboBox()
        self.combo_template.addItem("无模板", "")
        self.combo_template.addItem("软件开发团队", "software_team")
        self.combo_template.setToolTip("选择项目模板自动初始化团队")
        
        self.btn_new_project = TacticalButton("新建")
        self.btn_new_project.clicked.connect(self.create_project)
        bar.addWidget(self.inp_project)
        bar.addWidget(self.combo_template)
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
        self.btn_new_agent = TacticalButton("加人")
        self.btn_new_agent.clicked.connect(self.create_agent)
        self.btn_init_team = TacticalButton("一键组队")
        self.btn_init_team.setToolTip("为当前项目自动创建标准开发团队")
        self.btn_init_team.clicked.connect(self.init_team)
        self.agent_bar.addWidget(self.inp_role)
        self.agent_bar.addWidget(self.combo_model)
        self.agent_bar.addWidget(self.btn_new_agent)
        self.agent_bar.addWidget(self.btn_init_team)
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
        self.btn_back_chat = TacticalButton("返回")
        self.btn_back_chat.clicked.connect(self.close_requested.emit)
        bar.addWidget(lbl)
        bar.addStretch()
        bar.addWidget(self.btn_latest)
        bar.addWidget(self.btn_back_chat)
        layout.addLayout(bar)
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet(f"QTextEdit {{ background-color: {THEME.hex_to_rgba(THEME.get_color('background_tertiary'), 0.5)}; color: {THEME.get_color('text_primary')}; border: 1px solid {THEME.get_color('border')}; font-family: {THEME.fonts['family_code']}; }}")
        self.chat_history.setHtml(f"<div style='color:{THEME.get_color('text_secondary')}; text-align:center; margin-top:20px;'>请在左侧选择或新建项目以开始</div>")
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
        lbl = QLabel("云端文件")
        lbl.setStyleSheet(f"color: {THEME.get_color('accent')}; font-weight: bold; font-size: 16px;")
        
        self.btn_refresh_files = TacticalButton("刷新")
        self.btn_refresh_files.clicked.connect(self.refresh_files)
        
        h_files = QHBoxLayout()
        h_files.addWidget(lbl)
        h_files.addWidget(self.btn_refresh_files)
        layout.addLayout(h_files)
        
        self.files_list = QListWidget()
        self.files_list.itemDoubleClicked.connect(self.on_file_double_clicked)
        self.files_list.setStyleSheet(f"QListWidget {{ background-color: {THEME.get_color('background_tertiary')}; color: {THEME.get_color('text_primary')}; border: 1px solid {THEME.get_color('border')}; }}")
        layout.addWidget(self.files_list)

    def refresh_files(self):
        self.files_list.clear()
        if not self.client: return
        res = self.client.list_output_files()
        files = res.get("files", [])
        for f in files:
            name = f.get("name", "unknown")
            url = f.get("url", "")
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, url)
            self.files_list.addItem(item)

    def on_file_double_clicked(self, item):
        url = item.data(Qt.UserRole)
        if url:
            full_url = f"{self.client.base_url}{url}"
            webbrowser.open(full_url)

    def create_project(self):
        name = self.inp_project.text().strip() or "新项目"
        template = self.combo_template.currentData()
        result = self.client.create_project(name, template) if self.client else {}
        self.project_id = result.get("project_id", "")
        if self.project_id:
            self.inp_project.clear()
            self.refresh_projects_tree(self.project_id)
        else:
            QMessageBox.critical(self, "创建失败", "无法创建项目，请检查服务器连接。")

    def on_ws_message(self, data):
        """Handle WebSocket messages for Orchestration Feedback"""
        msg_type = data.get("type")
        if msg_type == "orchestration":
            status = data.get("status")
            message = data.get("message", "")
            project_id = data.get("project_id")
            
            # Enrich message based on status if empty
            if not message:
                if status == "step_start":
                    role = data.get("role", "Unknown")
                    task = data.get("task", "Unknown Task")
                    message = f"[{role}] 开始任务: {task}"
                elif status == "step_done":
                    role = data.get("role", "Unknown")
                    output = data.get("output", "")
                    # Truncate output for display
                    preview = output[:100] + "..." if len(output) > 100 else output
                    message = f"[{role}] 任务完成. 输出预览: {preview}"
                elif status == "plan_created":
                    tasks = data.get("tasks", [])
                    message = f"计划已生成，共 {len(tasks)} 个步骤。"
                elif status == "complete":
                    report = data.get("report", "")
                    message = "流程结束。报告已生成。"
                    if report:
                        # Append report separately or as part of message
                        pass 
                elif status == "error":
                    message = data.get("error", "Unknown Error")

            # Filter if current project (optional, currently showing all for demo)
            if self.project_id and project_id and project_id != self.project_id:
                pass # Or show notification
                
            # Append to chat with style
            color = THEME.get_color('accent')
            # Simple hex to rgba approximation or just use hex with opacity in css if supported
            # PyQt rich text supports basic CSS.
            
            html = f"""
            <table width="100%" style="margin-top: 10px; margin-bottom: 10px;">
                <tr>
                    <td style="border-left: 3px solid {color}; padding-left: 10px; background-color: rgba(0, 255, 0, 0.05);">
                        <div style="font-weight: bold; color: {color}; font-size: 11px;">SYSTEM // {status.upper()}</div>
                        <div style="margin-top: 4px; color: #CCCCCC;">{message}</div>
                    </td>
                </tr>
            </table>
            """
            self.chat_history.append(html)
            
            # If complete, maybe show the full report in viewer
            if status == "complete" and "report" in data:
                self.viewer.setPlainText(data["report"])
            
            if status == "complete":
                self.refresh_files()
            
            if status == "step_done":
                # Show result preview if available?
                pass


    def refresh_projects_tree(self, target_project_id=None):
        self.tree.clear()
        projects = self.client.list_projects().get("projects", []) if self.client else []
        target_item = None
        
        for p in projects:
            p_id = p.get("id","")
            p_item = QTreeWidgetItem([f"{p.get('name','')}"])
            p_item.setData(0, Qt.UserRole, ("project", p_id))
            self.tree.addTopLevelItem(p_item)
            
            grp = QTreeWidgetItem(["群聊"])
            grp.setData(0, Qt.UserRole, ("group", p_id))
            p_item.addChild(grp)
            
            if target_project_id and p_id == target_project_id:
                target_item = grp
                p_item.setExpanded(True)

            agents = self.client.list_agents(p_id).get("agents", []) if self.client else []
            for a in agents:
                a_item = QTreeWidgetItem([f"{a.get('role_name','')}"])
                a_item.setData(0, Qt.UserRole, ("agent", p_id, a.get("role_name","")))
                p_item.addChild(a_item)
        
        self.tree.expandAll()
        
        if target_item:
            self.tree.setCurrentItem(target_item)
            self.on_tree_clicked(target_item, 0)

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

    def init_team(self):
        if not self.project_id:
            QMessageBox.warning(self, "操作无效", "请先选择一个项目。")
            return
        r = self.client.init_team(self.project_id)
        if r.get("ok"):
            self.refresh_projects_tree(self.project_id)

    def send_chat(self):
        if not self.project_id:
            QMessageBox.warning(self, "未选择项目", "请先在左侧选择或新建一个项目以开始对话。")
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
