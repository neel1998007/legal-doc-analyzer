"""
Embedding Service for Legal Documents
Converts text chunks into vector embeddings
"""
from typing import List, Dict, Any, Optional
import numpy as np


class EmbeddingService:
    """Service for generating text embeddings"""

    # Use a lightweight but effective model
    MODEL_NAME = "all-MiniLM-L6-v2"
    
    # Singleton model instance
    _model = None

    @classmethod
    def get_model(cls):
        """
        Get or initialize the embedding model
        Uses singleton pattern to avoid loading model multiple times
        """
        if cls._model is None:
            print(f"🔄 Loading embedding model: {cls.MODEL_NAME}")
            try:
                from sentence_transformers import SentenceTransformer
                cls._model = SentenceTransformer(cls.MODEL_NAME)
                print(f"✅ Embedding model loaded successfully!")
            except Exception as e:
                print(f"❌ Error loading model: {e}")
                raise
        return cls._model

    @classmethod
    def generate_embedding(cls, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Input text

        Returns:
            List of floats representing the embedding
        """
        if not text or not text.strip():
            raise ValueError("Cannot generate embedding for empty text")

        model = cls.get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    @classmethod
    def generate_embeddings_batch(
        cls,
        texts: List[str],
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently

        Args:
            texts: List of input texts
            batch_size: Number of texts to process at once

        Returns:
            List of embeddings
        """
        if not texts:
            return []

        model = cls.get_model()

        print(f"🔄 Generating embeddings for {len(texts)} texts...")

        # Process in batches
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = model.encode(
                batch,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            all_embeddings.extend(batch_embeddings.tolist())

            # Show progress
            processed = min(i + batch_size, len(texts))
            print(f"  Processed {processed}/{len(texts)} texts")

        print(f"✅ Generated {len(all_embeddings)} embeddings")
        return all_embeddings

    @classmethod
    def embed_chunks(
        cls,
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Add embeddings to chunk objects

        Args:
            chunks: List of chunk dictionaries from ChunkingService

        Returns:
            Chunks with embeddings added
        """
        if not chunks:
            return []

        # Extract texts from chunks
        texts = [chunk["text"] for chunk in chunks]

        # Generate embeddings in batch
        embeddings = cls.generate_embeddings_batch(texts)

        # Add embeddings to chunks
        embedded_chunks = []
        for chunk, embedding in zip(chunks, embeddings):
            chunk_with_embedding = chunk.copy()
            chunk_with_embedding["embedding"] = embedding
            chunk_with_embedding["embedding_model"] = cls.MODEL_NAME
            chunk_with_embedding["embedding_dimension"] = len(embedding)
            embedded_chunks.append(chunk_with_embedding)

        return embedded_chunks

    @classmethod
    def calculate_similarity(
        cls,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score between 0 and 1
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)
        return float(similarity)

    @classmethod
    def find_most_similar(
        cls,
        query_embedding: List[float],
        chunk_embeddings: List[List[float]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find most similar chunks to a query

        Args:
            query_embedding: Query embedding vector
            chunk_embeddings: List of chunk embeddings
            top_k: Number of top results to return

        Returns:
            List of results with similarity scores
        """
        similarities = []

        for idx, chunk_embedding in enumerate(chunk_embeddings):
            similarity = cls.calculate_similarity(
                query_embedding,
                chunk_embedding
            )
            similarities.append({
                "index": idx,
                "similarity": similarity
            })

        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x["similarity"], reverse=True)

        return similarities[:top_k]