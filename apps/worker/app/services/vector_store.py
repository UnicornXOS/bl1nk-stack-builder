"""
Vector store for bl1nk-agent-builder
Handles vector storage and similarity search
"""

import logging
from typing import List, Dict, Any, Optional, Tuple

from app.config.settings import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Vector store for embeddings"""
    
    def __init__(self):
        self.embeddings = {}  # In-memory storage (would use pgvector in production)
        self.vectors = []
    
    async def store_embedding(
        self,
        text: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store embedding with metadata"""
        
        vector_id = f"vec_{len(self.vectors)}"
        
        vector_data = {
            "id": vector_id,
            "text": text,
            "embedding": embedding,
            "metadata": metadata or {},
            "created_at": "2024-01-01T00:00:00Z"  # Would use datetime.now()
        }
        
        self.vectors.append(vector_data)
        
        logger.info(
            f"Embedding stored: {vector_id}",
            extra={
                "event": "embedding_stored",
                "vector_id": vector_id,
                "dimension": len(embedding),
                "text_length": len(text)
            }
        )
        
        return vector_id
    
    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 5,
        threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Search for similar embeddings"""
        
        results = []
        
        # Simple cosine similarity (would use pgvector in production)
        for vector_data in self.vectors:
            similarity = self._cosine_similarity(query_embedding, vector_data["embedding"])
            
            if similarity >= threshold:
                results.append({
                    "id": vector_data["id"],
                    "text": vector_data["text"],
                    "metadata": vector_data["metadata"],
                    "similarity": similarity
                })
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:limit]
        
        logger.info(
            f"Vector search completed: {len(results)} results",
            extra={
                "event": "vector_search_completed",
                "total_vectors": len(self.vectors),
                "results_found": len(results),
                "threshold": threshold
            }
        )
        
        return results
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)