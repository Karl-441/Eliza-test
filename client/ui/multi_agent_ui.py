from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter, QTextEdit, QLineEdit, QComboBox, QTreeWidget, QTreeWidgetItem, QPlainTextEdit, QFileSystemModel, QTreeView, QListWidget, QListWidgetItem, QMessageBox, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QDir
from PyQt5.QtGui import QPainter, QColor, QPixmap, QIcon
from ..components import TacticalFrame, TacticalButton, ChatBubble, TacticalToast
from ..framework.theme import THEME
from ..framework.websocket import WebSocketClient
from ..framework.i18n import I18N
from .dag_visualizer import DAGWidget
from .task_detail_dialog import TaskDetailDialog
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
        
        I18N.language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()
        
    def retranslate_ui(self):
        # Projects Panel
        self.inp_project.setPlaceholderText(I18N.t("ma_new_project_name"))
        self.btn_new_project.setText(I18N.t("ma_btn_new"))
        self.combo_template.setItemText(0, I18N.t("ma_template_none"))
        self.combo_template.setItemText(1, I18N.t("ma_template_sw"))
        self.combo_template.setToolTip(I18N.t("ma_template_tooltip"))
        
        # Agent Bar
        self.inp_role.setPlaceholderText(I18N.t("ma_agent_role"))
        self.btn_new_agent.setText(I18N.t("ma_btn_add_agent"))
        self.btn_init_team.setText(I18N.t("ma_btn_init_team"))
        self.btn_init_team.setToolTip(I18N.t("ma_tooltip_init_team"))
        
        # Chat Panel
        if hasattr(self, 'lbl_chat'): self.lbl_chat.setText(I18N.t("ma_lbl_group_chat"))
        self.btn_latest.setText(I18N.t("ma_btn_latest"))
        self.btn_back_chat.setText(I18N.t("ma_btn_back"))
        self.btn_pause.setText(I18N.t("ma_btn_pause"))
        self.btn_resume.setText(I18N.t("ma_btn_resume"))
        self.btn_approve.setText(I18N.t("ma_btn_approve"))
        self.btn_reject.setText(I18N.t("ma_btn_reject"))
        self.inp_chat.setPlaceholderText(I18N.t("ma_input_placeholder"))
        self.btn_send_chat.setText(I18N.t("ma_btn_send"))
        
        # Viewer Panel
        if hasattr(self, 'tabs'):
            self.tabs.setTabText(0, I18N.t("ma_tab_dag"))
            self.tabs.setTabText(1, I18N.t("ma_tab_report"))
        
        # Files Panel
        if hasattr(self, 'lbl_files'): self.lbl_files.setText(I18N.t("ma_lbl_cloud_files"))
        self.btn_refresh_files.setText(I18N.t("ma_btn_refresh"))

    def setup_projects_panel(self):
        layout = QVBoxLayout(self.projects_panel)
        layout.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        self.inp_project = QLineEdit()
        self.inp_project.setPlaceholderText(I18N.t("ma_new_project_name"))
        
        # Template Selection
        self.combo_template = QComboBox()
        self.combo_template.addItem(I18N.t("ma_template_none"), "")
        self.combo_template.addItem(I18N.t("ma_template_sw"), "software_team")
        self.combo_template.setToolTip(I18N.t("ma_template_tooltip"))
        
        self.btn_new_project = TacticalButton(I18N.t("ma_btn_new"))
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
        self.inp_role.setPlaceholderText(I18N.t("ma_agent_role"))
        self.combo_model = QComboBox()
        self.combo_model.setEditable(True)
        self.btn_new_agent = TacticalButton(I18N.t("ma_btn_add_agent"))
        self.btn_new_agent.clicked.connect(self.create_agent)
        self.btn_init_team = TacticalButton(I18N.t("ma_btn_init_team"))
        self.btn_init_team.setToolTip(I18N.t("ma_tooltip_init_team"))
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
        self.lbl_chat = QLabel(I18N.t("ma_lbl_group_chat"))
        self.lbl_chat.setStyleSheet(f"color: {THEME.get_color('accent')}; font-weight: bold; font-size: 16px;")
        self.btn_latest = TacticalButton(I18N.t("ma_btn_latest"))
        self.btn_latest.set_accent_color(THEME.get_color('accent'))
        self.btn_latest.clicked.connect(self.scroll_chat_bottom)
        self.btn_back_chat = TacticalButton(I18N.t("ma_btn_back"))
        self.btn_back_chat.clicked.connect(self.close_requested.emit)
        bar.addWidget(self.lbl_chat)
        bar.addStretch()
        bar.addWidget(self.btn_latest)
        bar.addWidget(self.btn_back_chat)
        layout.addLayout(bar)

        # Control Bar
        self.control_bar = QHBoxLayout()
        self.btn_pause = TacticalButton(I18N.t("ma_btn_pause"))
        self.btn_pause.set_accent_color(THEME.get_color('warning'))
        self.btn_pause.clicked.connect(lambda: self.send_control("pause"))
        
        self.btn_resume = TacticalButton(I18N.t("ma_btn_resume"))
        self.btn_resume.set_accent_color(THEME.get_color('success'))
        self.btn_resume.clicked.connect(lambda: self.send_control("resume"))
        
        self.btn_approve = TacticalButton(I18N.t("ma_btn_approve"))
        self.btn_approve.set_accent_color(THEME.get_color('success'))
        self.btn_approve.clicked.connect(lambda: self.send_control("approve"))
        self.btn_approve.hide()
        
        self.btn_reject = TacticalButton(I18N.t("ma_btn_reject"))
        self.btn_reject.set_accent_color(THEME.get_color('error'))
        self.btn_reject.clicked.connect(lambda: self.send_control("reject"))
        self.btn_reject.hide()
        
        self.control_bar.addWidget(self.btn_pause)
        self.control_bar.addWidget(self.btn_resume)
        self.control_bar.addStretch()
        self.control_bar.addWidget(self.btn_reject)
        self.control_bar.addWidget(self.btn_approve)
        layout.addLayout(self.control_bar)

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet(f"QTextEdit {{ background-color: {THEME.hex_to_rgba(THEME.get_color('background_tertiary'), 0.5)}; color: {THEME.get_color('text_primary')}; border: 1px solid {THEME.get_color('border')}; font-family: {THEME.fonts['family_code']}; }}")
        self.chat_history.setHtml(f"<div style='color:{THEME.get_color('text_secondary')}; text-align:center; margin-top:20px;'>{I18N.t('ma_placeholder_chat')}</div>")
        layout.addWidget(self.chat_history)
        self.inp_chat = QLineEdit()
        self.inp_chat.setPlaceholderText(I18N.t("ma_input_placeholder"))
        self.btn_send_chat = TacticalButton(I18N.t("ma_btn_send"))
        self.btn_send_chat.clicked.connect(self.send_chat)
        h = QHBoxLayout()
        h.addWidget(self.inp_chat)
        h.addWidget(self.btn_send_chat)
        layout.addLayout(h)
    def send_control(self, action):
        if not self.project_id: return
        res = self.client.control_workflow(self.project_id, action)
        if res.get("status") == "command_sent":
            TacticalToast.show_toast(self, I18N.t("ma_toast_cmd_sent").format(action), "info")
            if action in ["approve", "reject"]:
                self.btn_approve.hide()
                self.btn_reject.hide()
        else:
            TacticalToast.show_toast(self, I18N.t("ma_toast_cmd_fail").format(res.get('error')), "error")

    def scroll_chat_bottom(self):
        self.chat_history.moveCursor(self.chat_history.textCursor().End)
        
    def setup_viewer_panel(self):
        layout = QVBoxLayout(self.viewer_panel)
        layout.setContentsMargins(0,0,0,0)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {THEME.get_color('border')}; }}
            QTabBar::tab {{ background: {THEME.get_color('background_secondary')}; color: {THEME.get_color('text_secondary')}; padding: 8px 12px; }}
            QTabBar::tab:selected {{ background: {THEME.get_color('background_tertiary')}; color: {THEME.get_color('accent')}; border-bottom: 2px solid {THEME.get_color('accent')}; }}
        """)
        
        # Tab 1: DAG
        self.dag_widget = DAGWidget()
        self.dag_widget.btn_refresh.clicked.connect(self.refresh_workflow_view)
        self.dag_widget.view.node_clicked.connect(self.show_task_detail)
        self.tabs.addTab(self.dag_widget, I18N.t("ma_tab_dag"))
        
        # Tab 2: Report/Log
        self.report_viewer = QPlainTextEdit()
        self.report_viewer.setReadOnly(True)
        self.report_viewer.setStyleSheet(f"background-color: {THEME.get_color('background_tertiary')}; color: {THEME.get_color('text_primary')}; border: none; font-family: {THEME.fonts['family_code']};")
        self.tabs.addTab(self.report_viewer, I18N.t("ma_tab_report"))
        
        layout.addWidget(self.tabs)
        
    def refresh_workflow_view(self):
        if not self.project_id: return
        try:
             import requests
             url = f"{self.client.base_url}/api/v1/projects/{self.project_id}/workflow"
             headers = self.client._get_headers()
             res = requests.get(url, headers=headers)
             if res.status_code == 200:
                 data = res.json()
                 tasks = data.get("tasks", [])
                 self.dag_widget.view.update_graph(tasks)
                 # Update agent status in tree based on tasks
                 self.update_agent_status(tasks)
        except Exception as e:
             print(f"Workflow fetch error: {e}")

    def show_task_detail(self, task_id):
        # Find task data from DAG visualizer cache
        tasks = self.dag_widget.view.tasks_data
        task = next((t for t in tasks if t['id'] == task_id), None)
        if task:
            dialog = TaskDetailDialog(self, task)
            dialog.exec_()

    def get_status_icon(self, status):
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        color = THEME.get_color("text_secondary")
        if status == "working":
            color = THEME.get_color("accent")
        elif status == "error":
            color = THEME.get_color("error")
        elif status == "online":
            color = THEME.get_color("success")
            
        painter.setBrush(QColor(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(3, 3, 10, 10)
        painter.end()
        return QIcon(pixmap)

    def update_agent_status(self, tasks):
        # Map roles to status
        role_status = {}
        for t in tasks:
            role = t.get("role")
            status = t.get("status")
            if not role: continue
            
            if status == "in_progress":
                role_status[role] = "working"
            elif status == "error":
                role_status[role] = "error"
            elif status == "completed" and role_status.get(role) != "working":
                 role_status[role] = "online"
        
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            p_item = root.child(i)
            p_data = p_item.data(0, Qt.UserRole) # ("project", p_id)
            if not p_data or p_data[1] != self.project_id:
                continue
            
            # Found current project
            for j in range(p_item.childCount()):
                a_item = p_item.child(j)
                # data is ("agent", p_id, role_name)
                a_data = a_item.data(0, Qt.UserRole)
                if not a_data: continue
                
                role = a_data[2]
                status = role_status.get(role, "idle")
                a_item.setIcon(0, self.get_status_icon(status))
                
                # Update tooltip
                a_item.setToolTip(0, f"Status: {status.upper()}")

    def setup_files_panel(self):
        layout = QVBoxLayout(self.files_panel)
        self.lbl_files = QLabel(I18N.t("ma_lbl_cloud_files"))
        self.lbl_files.setStyleSheet(f"color: {THEME.get_color('accent')}; font-weight: bold; font-size: 16px;")
        
        self.btn_refresh_files = TacticalButton(I18N.t("ma_btn_refresh"))
        self.btn_refresh_files.clicked.connect(self.refresh_files)
        
        h_files = QHBoxLayout()
        h_files.addWidget(self.lbl_files)
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
        name = self.inp_project.text().strip() or I18N.t("ma_default_project")
        template = self.combo_template.currentData()
        result = self.client.create_project(name, template) if self.client else {}
        self.project_id = result.get("project_id", "")
        if self.project_id:
            self.inp_project.clear()
            self.refresh_projects_tree(self.project_id)
            TacticalToast.show_toast(self, I18N.t("ma_toast_project_created"), "success")
        else:
            TacticalToast.show_toast(self, I18N.t("ma_toast_create_fail"), "error")

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
                    message = I18N.t("ma_task_start").format(role, task)
                elif status == "step_done":
                    role = data.get("role", "Unknown")
                    output = data.get("output", "")
                    # Truncate output for display
                    preview = output[:100] + "..." if len(output) > 100 else output
                    message = I18N.t("ma_task_done").format(role, preview)
                    TacticalToast.show_toast(self, f"Task Done: {role}", "success")
                elif status == "plan_created":
                    tasks = data.get("tasks", [])
                    message = I18N.t("ma_plan_created").format(len(tasks))
                    TacticalToast.show_toast(self, f"Plan: {len(tasks)} steps", "info")
                elif status == "complete":
                    report = data.get("report", "")
                    message = I18N.t("ma_workflow_end")
                    if report:
                        # Append report separately or as part of message
                        pass 
                elif status == "error":
                    message = data.get("error", "Unknown Error")
                    TacticalToast.show_toast(self, f"Error: {message[:30]}...", "error")
                elif status == "waiting_for_approval":
                    message = I18N.t("ma_workflow_paused")
                    TacticalToast.show_toast(self, I18N.t("ma_toast_need_approval"), "warning")
                    self.btn_approve.show()
                    self.btn_reject.show()

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
                self.report_viewer.setPlainText(data["report"])
                self.tabs.setCurrentWidget(self.report_viewer)

            if status in ["plan_created", "step_start", "step_done", "waiting_for_approval", "complete"]:
                self.refresh_workflow_view()
            
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
            
            grp = QTreeWidgetItem([I18N.t("ma_lbl_group_chat")])
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
        role = self.inp_role.text().strip() or I18N.t("role_executor")
        model = self.combo_model.currentData() or "server-qwen2.5-7b"
        desc = ""
        r = self.client.create_agent(self.project_id, role, model, desc)
        if r.get("ok"):
            self.refresh_projects_tree()

    def init_team(self):
        if not self.current_project_id:
            TacticalToast.show_toast(self, I18N.t("toast_select_project_first"), "warning")
            return
        r = self.client.init_team(self.project_id)
        if r.get("ok"):
            self.refresh_projects_tree(self.project_id)
            TacticalToast.show_toast(self, I18N.t("toast_team_init"), "success")

    def send_chat(self):
        if not self.project_id:
            TacticalToast.show_toast(self, "请先在左侧选择或新建一个项目以开始对话。", "warning")
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
