from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from server.core.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, index=True)
    owner_key = Column(String, index=True)
    owner_user = Column(String, index=True, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to agents
    agents = relationship("Agent", back_populates="project", cascade="all, delete-orphan")
    logs = relationship("ProjectLog", back_populates="project", cascade="all, delete-orphan")

class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"))
    role_name = Column(String)
    model_name = Column(String)
    description = Column(Text)
    system_prompt = Column(Text)
    
    project = relationship("Project", back_populates="agents")

class ProjectLog(Base):
    __tablename__ = "project_logs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String, default="INFO")
    message = Column(Text)
    
    project = relationship("Project", back_populates="logs")

class WorkflowState(Base):
    __tablename__ = "workflow_states"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"))
    status = Column(String, default="pending")  # pending, running, paused, completed, failed
    tasks = Column(Text)  # JSON string of tasks with status
    context = Column(Text)  # JSON/Text context
    outputs = Column(Text)  # JSON string of outputs
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

