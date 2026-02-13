from sqlalchemy import select, text
from sqlalchemy.orm import Session
from server.core.database import SessionLocal, engine
from server.core.memory.models import InstinctMemory, SubconsciousMemory, ActiveRecallMemory
from server.core.memory.embedding import embedding_service
from server.core.config import settings
import logging
import numpy as np

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.ensure_extension()
        self.is_sqlite = not settings.database_url.startswith("postgresql")
        
    def ensure_extension(self):
        if settings.database_url.startswith("postgresql"):
            try:
                with engine.connect() as conn:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                    conn.commit()
            except Exception as e:
                logger.warning(f"Failed to create vector extension: {e}")

    def get_all_memories(self, layer_name: str):
        with SessionLocal() as db:
            if layer_name == "instinct":
                return db.query(InstinctMemory).all()
            elif layer_name == "subconscious":
                return db.query(SubconsciousMemory).all()
            elif layer_name == "active_recall":
                return db.query(ActiveRecallMemory).all()
            return []

    def _cosine_similarity_py(self, vec1, vec2):
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

    def _search_sqlite(self, model, query_embedding, limit, threshold=0.0):
        with SessionLocal() as db:
            all_memories = db.query(model).all()
        
        if not all_memories:
            return []

        # Filter out empty embeddings
        valid_memories = [m for m in all_memories if m.embedding]
        if not valid_memories:
            return []
            
        try:
            # Vectorized calculation for performance
            matrix = np.array([m.embedding for m in valid_memories]) # Shape (N, D)
            query = np.array(query_embedding) # Shape (D,)
            
            # Normalize
            norm_matrix = np.linalg.norm(matrix, axis=1)
            norm_query = np.linalg.norm(query)
            
            if norm_query == 0:
                return []
                
            # Avoid division by zero
            norm_matrix[norm_matrix == 0] = 1e-10
            
            # Cosine similarity
            dot_products = np.dot(matrix, query)
            similarities = dot_products / (norm_matrix * norm_query)
            
            # Collect results
            results = []
            for i, sim in enumerate(similarities):
                if sim >= threshold:
                    results.append({"memory": valid_memories[i], "similarity": float(sim)})
            
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            # Fallback to slow loop if numpy fails for some reason
            results = []
            for mem in valid_memories:
                sim = self._cosine_similarity_py(query_embedding, mem.embedding)
                if sim >= threshold:
                    results.append({"memory": mem, "similarity": sim})
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:limit]

    # Instinct Layer
    def add_instinct(self, content: str, trait_type: str, strength: float = 1.0):
        embedding = embedding_service.get_embedding(content)
        with SessionLocal() as db:
            memory = InstinctMemory(
                content=content,
                embedding=embedding,
                trait_type=trait_type,
                strength=strength
            )
            db.add(memory)
            db.commit()
            db.refresh(memory)
            return memory

    def search_instinct(self, query_text: str, limit: int = 5, threshold: float = 0.85):
        embedding = embedding_service.get_embedding(query_text)
        
        if self.is_sqlite:
            return self._search_sqlite(InstinctMemory, embedding, limit, threshold)

        with SessionLocal() as db:
            try:
                distance_threshold = 1 - threshold
                stmt = select(InstinctMemory, InstinctMemory.embedding.cosine_distance(embedding).label("distance")) \
                    .filter(InstinctMemory.embedding.cosine_distance(embedding) < distance_threshold) \
                    .order_by("distance") \
                    .limit(limit)
                    
                results = db.execute(stmt).all()
                return [{"memory": r[0], "similarity": 1 - r[1]} for r in results]
            except Exception as e:
                logger.error(f"Error searching instinct memory: {e}")
                return []

    # Subconscious Layer
    def add_subconscious(self, content: str, keywords: str):
        embedding = embedding_service.get_embedding(content)
        with SessionLocal() as db:
            memory = SubconsciousMemory(
                content=content,
                embedding=embedding,
                keywords=keywords
            )
            db.add(memory)
            db.commit()
            db.refresh(memory)
            return memory

    def search_subconscious(self, query_text: str, limit: int = 5, threshold: float = 0.7):
        embedding = embedding_service.get_embedding(query_text)
        
        if self.is_sqlite:
            return self._search_sqlite(SubconsciousMemory, embedding, limit, threshold)

        with SessionLocal() as db:
            try:
                distance_threshold = 1 - threshold
                stmt = select(SubconsciousMemory, SubconsciousMemory.embedding.cosine_distance(embedding).label("distance")) \
                    .filter(SubconsciousMemory.embedding.cosine_distance(embedding) < distance_threshold) \
                    .order_by("distance") \
                    .limit(limit)
                    
                results = db.execute(stmt).all()
                return [{"memory": r[0], "similarity": 1 - r[1]} for r in results]
            except Exception as e:
                logger.error(f"Error searching subconscious memory: {e}")
                return []

    # Active Recall Layer
    def add_active_recall(self, content: str, role: str, context_metadata: dict = None):
        embedding = embedding_service.get_embedding(content)
        with SessionLocal() as db:
            memory = ActiveRecallMemory(
                content=content,
                embedding=embedding,
                role=role,
                context_metadata=context_metadata or {}
            )
            db.add(memory)
            db.commit()
            db.refresh(memory)
            return memory

    def search_active_recall(self, query_text: str, limit: int = 5, time_range: dict = None):
        embedding = embedding_service.get_embedding(query_text)
        
        if self.is_sqlite:
            # Active recall usually doesn't need strict threshold for "search", just top-k
            return self._search_sqlite(ActiveRecallMemory, embedding, limit, threshold=0.0)

        with SessionLocal() as db:
            try:
                stmt = select(ActiveRecallMemory, ActiveRecallMemory.embedding.cosine_distance(embedding).label("distance")) \
                    .order_by("distance") \
                    .limit(limit)
                
                # TODO: Add time range filter implementation
                
                results = db.execute(stmt).all()
                return [{"memory": r[0], "similarity": 1 - r[1]} for r in results]
            except Exception as e:
                logger.error(f"Error searching active recall memory: {e}")
                return []

    def delete_memory(self, layer_name: str, memory_id: int):
        with SessionLocal() as db:
            if layer_name == "instinct":
                model = InstinctMemory
            elif layer_name == "subconscious":
                model = SubconsciousMemory
            elif layer_name == "active_recall":
                model = ActiveRecallMemory
            else:
                return False
                
            memory = db.query(model).filter(model.id == memory_id).first()
            if memory:
                db.delete(memory)
                db.commit()
                return True
            return False

    def get_all_memories(self, layer: str):
        with SessionLocal() as db:
            if layer == "instinct":
                return db.query(InstinctMemory).all()
            elif layer == "subconscious":
                return db.query(SubconsciousMemory).all()
            elif layer == "active_recall":
                return db.query(ActiveRecallMemory).all()
            return []

vector_store = VectorStore()
