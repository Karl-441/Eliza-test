import json
import os
import uuid
from pathlib import Path
from typing import Dict, List
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "projects.json"

class ProjectsStore:
    def __init__(self):
        self.projects: Dict[str, dict] = {}
        self.load()

    def load(self):
        try:
            if os.path.exists(DB_PATH):
                with open(DB_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.projects = {p["id"]: p for p in data}
        except:
            self.projects = {}

    def save(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(list(self.projects.values()), f, indent=2, ensure_ascii=False)

    def create_project(self, name: str, owner_key: str) -> dict:
        pid = str(uuid.uuid4())
        proj = {"id": pid, "name": name or "新项目", "owner_key": owner_key, "created_at": datetime.now().isoformat(), "agents": []}
        self.projects[pid] = proj
        self.save()
        return {"project_id": pid}

    def list_projects(self, owner_key: str) -> dict:
        items = [p for p in self.projects.values() if p.get("owner_key") == owner_key]
        return {"projects": items}

    def add_agent(self, project_id: str, role_name: str, model_name: str, description: str) -> dict:
        p = self.projects.get(project_id)
        if not p:
            return {"error": "project_not_found"}
        agents: List[dict] = p.get("agents", [])
        if "总负责人" not in [a.get("role_name") for a in agents] and role_name != "总负责人":
            return {"error": "need_coordinator_first"}
        agent = {"role_name": role_name, "model_name": model_name, "description": description, "created_at": datetime.now().isoformat()}
        agents.append(agent)
        p["agents"] = agents
        self.projects[project_id] = p
        self.save()
        return {"ok": True}

    def list_agents(self, project_id: str) -> dict:
        p = self.projects.get(project_id)
        if not p:
            return {"agents": []}
        return {"agents": p.get("agents", [])}

projects_store = ProjectsStore()
