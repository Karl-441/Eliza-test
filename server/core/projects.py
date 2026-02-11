import logging
from typing import Dict, List, Optional
from datetime import datetime
from threading import RLock
from sqlalchemy.orm import Session
from .config import settings
from .database import SessionLocal, engine, Base
from .models import Project, Agent, ProjectLog

# Initialize Database
Base.metadata.create_all(bind=engine)

class ProjectsStore:
    def __init__(self):
        # We no longer need in-memory dict for everything, but we can keep cache if needed.
        # For this refactor, we will go direct to DB to ensure persistence.
        self.lock = RLock() # Still useful for critical sections if mixed with memory, but DB handles concurrency mostly.
        
    def _get_db(self) -> Session:
        return SessionLocal()

    def create_project(self, name: str, owner_key: str, owner_user: str = "", template: str = "") -> dict:
        db = self._get_db()
        try:
            new_project = Project(
                name=name or "新项目",
                owner_key=owner_key,
                owner_user=owner_user,
                created_at=datetime.utcnow()
            )
            db.add(new_project)
            db.commit()
            db.refresh(new_project)
            
            project_id = new_project.id
            
            # Auto-initialize based on template
            if template == "software_team":
                self.init_dev_team(project_id, db_session=db)
                
            return {"project_id": project_id}
        finally:
            db.close()

    def list_all(self) -> dict:
        db = self._get_db()
        try:
            projects = db.query(Project).all()
            return {"projects": [self._project_to_dict(p) for p in projects]}
        finally:
            db.close()

    def list_by_owner_user(self, owner_user: str) -> dict:
        db = self._get_db()
        try:
            projects = db.query(Project).filter(Project.owner_user == owner_user).all()
            return {"projects": [self._project_to_dict(p) for p in projects]}
        finally:
            db.close()

    def list_projects(self, owner_key: str) -> dict:
        db = self._get_db()
        try:
            projects = db.query(Project).filter(Project.owner_key == owner_key).all()
            return {"projects": [self._project_to_dict(p) for p in projects]}
        finally:
            db.close()
            
    def get_project(self, project_id: str) -> Optional[dict]:
        db = self._get_db()
        try:
            p = db.query(Project).filter(Project.id == project_id).first()
            return self._project_to_dict(p) if p else None
        finally:
            db.close()

    def add_agent(self, project_id: str, role_name: str, model_name: str, description: str, system_prompt: str = "") -> dict:
        db = self._get_db()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"error": "project_not_found"}
            
            agent = Agent(
                project_id=project_id,
                role_name=role_name,
                model_name=model_name,
                description=description,
                system_prompt=system_prompt
            )
            db.add(agent)
            db.commit()
            return {"ok": True}
        finally:
            db.close()

    def init_dev_team(self, project_id: str, db_session: Session = None) -> dict:
        """Initialize a standard software development team for the project."""
        close_session = False
        if db_session:
            db = db_session
        else:
            db = self._get_db()
            close_session = True
            
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"error": "project_not_found"}

            # Clear existing agents
            db.query(Agent).filter(Agent.project_id == project_id).delete()
            
            team = [
                {
                    "role_name": "Product Manager",
                    "model_name": settings.default_model_name,
                    "description": "负责需求分析和任务规划",
                    "system_prompt": "你是产品经理。你的职责是分析用户需求，将其转化为清晰的功能规格说明书。请用结构化的方式描述功能点。"
                },
                {
                    "role_name": "Architect",
                    "model_name": settings.default_model_name,
                    "description": "负责系统架构设计和技术选型",
                    "system_prompt": "你是系统架构师。请设计系统的整体架构，选择合适的技术栈，并解释原因。"
                },
                {
                    "role_name": "Coder",
                    "model_name": settings.default_model_name,
                    "description": "负责代码实现",
                    "system_prompt": "你是高级开发工程师。请根据需求和架构编写高质量的代码。代码需要包含注释。"
                },
                {
                    "role_name": "Tester",
                    "model_name": settings.default_model_name,
                    "description": "负责测试用例编写和代码审查",
                    "system_prompt": "你是QA工程师。请编写测试用例，并检查代码的逻辑错误和潜在bug。"
                }
            ]
            
            for m in team:
                agent = Agent(
                    project_id=project_id,
                    role_name=m["role_name"],
                    model_name=m["model_name"],
                    description=m["description"],
                    system_prompt=m["system_prompt"]
                )
                db.add(agent)
            
            db.commit()
            return {"ok": True, "message": "Dev team initialized"}
        except Exception as e:
            db.rollback()
            logging.error(f"Error init dev team: {e}")
            return {"error": str(e)}
        finally:
            if close_session:
                db.close()

    def list_agents(self, project_id: str) -> dict:
        db = self._get_db()
        try:
            agents = db.query(Agent).filter(Agent.project_id == project_id).all()
            return {"agents": [self._agent_to_dict(a) for a in agents]}
        finally:
            db.close()

    def get_log(self, project_id: str) -> dict:
        db = self._get_db()
        try:
            logs = db.query(ProjectLog).filter(ProjectLog.project_id == project_id).order_by(ProjectLog.timestamp).all()
            return {"logs": [{"timestamp": l.timestamp.isoformat(), "level": l.level, "message": l.message} for l in logs]}
        finally:
            db.close()
            
    def add_log(self, project_id: str, message: str, level: str = "INFO"):
        db = self._get_db()
        try:
            log = ProjectLog(project_id=project_id, message=message, level=level)
            db.add(log)
            db.commit()
        finally:
            db.close()

    def _project_to_dict(self, p: Project) -> dict:
        return {
            "id": p.id,
            "name": p.name,
            "owner_key": p.owner_key,
            "owner_user": p.owner_user,
            "created_at": p.created_at.isoformat() if p.created_at else "",
            "agents": [self._agent_to_dict(a) for a in p.agents]
        }
        
    def _agent_to_dict(self, a: Agent) -> dict:
        return {
            "id": a.id,
            "role_name": a.role_name,
            "model_name": a.model_name,
            "description": a.description,
            "system_prompt": a.system_prompt
        }

projects_store = ProjectsStore()
