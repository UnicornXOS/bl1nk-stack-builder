"""
Embeddings client for bl1nk-agent-builder
Handles embedding generation and caching
"""

import asyncio
import hashlib
import logging
from typing import List, Optional

from app.config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """Client for generating embeddings"""
    
    def __init__(self):
        self.cache = {}
    
    async def generate_embedding(
        self, 
        text: str, 
        model: str = "gamma-300"
    ) -> List[float]:
        """Generate embedding for text"""
        
        # Check cache first
        cache_key = self._get_cache_key(text, model)
        if cache_key in self.cache:
            logger.debug("Embedding cache hit")
            return self.cache[cache_key]
        
        # Generate embedding (placeholder)
        await asyncio.sleep(0.1)  # Simulate API call
        
        # Mock embedding (768 dimensions)
        import random
        embedding = [random.uniform(-1, 1) for _ in range(768)]
        
        # Cache the result
        self.cache[cache_key] = embedding
        
        logger.info(
            f"Embedding generated for text (length: {len(text)})",
            extra={
                "event": "embedding_generated",
                "model": model,
                "text_length": len(text),
                "dimension": len(embedding)
            }
        )
        
        return embedding
    
    def _get_cache_key(self, text: str, model: str) -> str:
        """Generate cache key for text and model"""
        
        content = f"{model}:{text}"
        return hashlib.md5(content.encode()).hexdigest()