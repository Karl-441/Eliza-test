from sqlalchemy import Column, String, Float, JSON, Integer, DateTime, ForeignKey, Text, Index, TypeDecorator
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from server.core.database import Base
from server.core.config import settings
import datetime
import uuid
import json

def generate_uuid():
    return str(uuid.uuid4())

# Compatibility for SQLite
class VectorType(TypeDecorator):
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return Vector(settings.vector_dim)
        return self.impl

    def process_bind_param(self, value, dialect):
        if dialect.name == 'postgresql':
            return value
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if dialect.name == 'postgresql':
            return value
        if value is None:
            return None
        return json.loads(value)

class InstinctMemory(Base):
    __tablename__ = "memory_instinct"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(VectorType)
    trait_type: Mapped[str] = mapped_column(String)  # e.g. "personality", "preference"
    strength: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # IVFFlat index for fast approximate search (Instinct layer needs speed)
    if settings.database_url.startswith("postgresql"):
        __table_args__ = (
            Index('idx_instinct_embedding', embedding, postgresql_using='ivfflat', postgresql_with={'lists': 100}, postgresql_ops={'embedding': 'vector_cosine_ops'}),
        )

class SubconsciousMemory(Base):
    __tablename__ = "memory_subconscious"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(VectorType)
    keywords: Mapped[str] = mapped_column(Text)  # Comma separated keywords for hybrid search
    association_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    
    # HNSW index for high recall (Subconscious needs accuracy)
    if settings.database_url.startswith("postgresql"):
        __table_args__ = (
            Index('idx_subconscious_embedding', embedding, postgresql_using='hnsw', postgresql_with={'m': 16, 'ef_construction': 64}, postgresql_ops={'embedding': 'vector_cosine_ops'}),
        )

class ActiveRecallMemory(Base):
    __tablename__ = "memory_active_recall"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(VectorType)
    role: Mapped[str] = mapped_column(String) # user or assistant
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    context_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    if settings.database_url.startswith("postgresql"):
        __table_args__ = (
            Index('idx_active_embedding', embedding, postgresql_using='ivfflat', postgresql_with={'lists': 100}, postgresql_ops={'embedding': 'vector_cosine_ops'}),
            Index('idx_active_metadata', context_metadata, postgresql_using='gin'),
        )
