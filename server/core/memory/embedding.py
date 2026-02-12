from typing import List
import os
from server.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.client = None
        self.local_model = None
        self.provider = settings.embedding_provider
        self._setup_client()

    def _setup_client(self):
        if self.provider == "openai":
            try:
                from openai import OpenAI
                api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
                if api_key:
                    self.client = OpenAI(
                        api_key=api_key,
                        base_url=settings.openai_base_url
                    )
            except ImportError:
                logger.error("openai package not installed.")
                
        elif self.provider == "local":
            try:
                from sentence_transformers import SentenceTransformer
                # Use default cache folder or specify one if needed
                self.local_model = SentenceTransformer(settings.local_embedding_model)
                logger.info(f"Loaded local embedding model: {settings.local_embedding_model}")
            except ImportError:
                logger.error("sentence-transformers not installed. Please install it to use local embeddings.")
            except Exception as e:
                logger.error(f"Failed to load local embedding model: {e}")

    def get_embedding(self, text: str) -> List[float]:
        if self.provider == "openai":
            if not self.client:
                self._setup_client()
            if not self.client:
                logger.warning("OpenAI client not configured. Returning zero vector.")
                return [0.0] * settings.vector_dim
            try:
                response = self.client.embeddings.create(
                    input=text.replace("\n", " "),
                    model=settings.embedding_model
                )
                return response.data[0].embedding
            except Exception as e:
                logger.error(f"Error generating embedding (OpenAI): {e}")
                return [0.0] * settings.vector_dim
        
        elif self.provider == "local":
            if not self.local_model:
                self._setup_client()
            if not self.local_model:
                logger.warning("Local model not loaded. Returning zero vector.")
                return [0.0] * settings.vector_dim
            try:
                # encode returns numpy array, convert to list
                embedding = self.local_model.encode(text)
                return embedding.tolist()
            except Exception as e:
                logger.error(f"Error generating embedding (Local): {e}")
                return [0.0] * settings.vector_dim
        
        return [0.0] * settings.vector_dim

embedding_service = EmbeddingService()
