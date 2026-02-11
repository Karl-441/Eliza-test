import logging
from typing import Dict, List, Optional
from datetime import datetime
from threading import RLock
from sqlalchemy.orm import Session
from .config import settings
from .database import SessionLocal, engine, Base
from .models import Project, Agent, ProjectLog
from .i18n import I18N

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
                name=name or I18N.t("default_new_project_name"),
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
                return {"error": I18N.t("project_not_found")}
            
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
                    "description": I18N.t("role_pm_desc"),
                    "system_prompt": I18N.t("role_pm_prompt")
                },
                {
                    "role_name": "Architect",
                    "model_name": settings.default_model_name,
                    "description": I18N.t("role_arch_desc"),
                    "system_prompt": I18N.t("role_arch_prompt")
                },
                {
                    "role_name": "Developer",
                    "model_name": settings.default_model_name,
                    "description": I18N.t("role_dev_desc"),
                    "system_prompt": I18N.t("role_dev_prompt")
                },
                {
                    "role_name": "QA Engineer",
                    "model_name": settings.default_model_name,
                    "description": I18N.t("role_qa_desc"),
                    "system_prompt": I18N.t("role_qa_prompt")
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
