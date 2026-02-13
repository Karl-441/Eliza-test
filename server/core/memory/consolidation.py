import time
import logging
from sqlalchemy import select, func, text
from server.core.database import SessionLocal
from server.core.memory.models import ActiveRecallMemory, SubconsciousMemory
from server.core.memory.vector_store import vector_store
from server.core.memory.embedding import embedding_service

logger = logging.getLogger(__name__)

class MemoryConsolidator:
    def __init__(self):
        self.batch_size = 50
        self.similarity_threshold = 0.92  # Very high similarity for merging

    def run_consolidation(self):
        """
        Main consolidation process:
        1. Identify redundant active memories
        2. Merge them into subconscious patterns
        3. Prune old/weak memories
        """
        logger.info("Starting memory consolidation...")
        try:
            self._consolidate_active_to_subconscious()
            self._prune_weak_memories()
            logger.info("Memory consolidation complete.")
        except Exception as e:
            logger.error(f"Error during consolidation: {e}")

    def _consolidate_active_to_subconscious(self):
        """
        Find clusters of similar active memories and convert them into a single subconscious pattern.
        """
        with SessionLocal() as db:
            # Get recent active memories that haven't been consolidated
            recent_memories = db.query(ActiveRecallMemory).order_by(ActiveRecallMemory.timestamp.desc()).limit(100).all()
            
            if len(recent_memories) < 2:
                return

            # Extract embeddings and ids
            memories_with_embedding = [m for m in recent_memories if m.embedding is not None]
            if not memories_with_embedding:
                return

            # Simple clustering based on cosine similarity
            clusters = []
            processed_ids = set()

            for i, mem1 in enumerate(memories_with_embedding):
                if mem1.id in processed_ids:
                    continue

                cluster = [mem1]
                processed_ids.add(mem1.id)
                
                # Compare with others
                for j in range(i + 1, len(memories_with_embedding)):
                    mem2 = memories_with_embedding[j]
                    if mem2.id in processed_ids:
                        continue
                    
                    sim = vector_store._cosine_similarity_py(mem1.embedding, mem2.embedding)
                    if sim >= self.similarity_threshold:
                        cluster.append(mem2)
                        processed_ids.add(mem2.id)
                
                if len(cluster) >= 3:  # Only consolidate if we have a meaningful cluster
                    clusters.append(cluster)

            # Process clusters into subconscious memories
            for cluster in clusters:
                # 1. Generate summary (In production, use LLM)
                # For now, we use the most recent memory's content as base + count
                base_content = cluster[0].content
                summary = f"Repeated pattern ({len(cluster)} times): {base_content}"
                
                # 2. Extract keywords (Simple heuristic)
                keywords = "pattern, consolidation" 
                
                # 3. Add to subconscious
                vector_store.add_subconscious(summary, keywords)
                logger.info(f"Consolidated {len(cluster)} memories into subconscious: {summary[:50]}...")

                # 4. Mark active memories as consolidated (or delete depending on policy)
                # For this implementation, we'll delete them to keep active memory clean
                for mem in cluster:
                    db.delete(mem)
            
            db.commit()

    def _prune_weak_memories(self):
        """
        Remove old active recall memories that haven't been accessed or reinforced.
        """
        import datetime
        
        # Retention policy: Keep last 1000 messages or 30 days
        # For this implementation, we delete memories older than 30 days
        retention_days = 30
        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=retention_days)
        
        with SessionLocal() as db:
            try:
                # Find old memories
                deleted_count = db.query(ActiveRecallMemory).filter(ActiveRecallMemory.timestamp < cutoff_date).delete()
                
                # Also keep total count under control (e.g., max 2000 active memories)
                total_count = db.query(ActiveRecallMemory).count()
                if total_count > 2000:
                    # Remove oldest excess
                    excess = total_count - 2000
                    subquery = db.query(ActiveRecallMemory.id).order_by(ActiveRecallMemory.timestamp.asc()).limit(excess)
                    db.query(ActiveRecallMemory).filter(ActiveRecallMemory.id.in_(subquery)).delete(synchronize_session=False)
                    deleted_count += excess
                
                if deleted_count > 0:
                    db.commit()
                    logger.info(f"Pruned {deleted_count} weak memories.")
            except Exception as e:
                logger.error(f"Error pruning memories: {e}")
                db.rollback()

memory_consolidator = MemoryConsolidator()
