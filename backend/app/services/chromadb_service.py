"""
ChromaDB Service for Legal Documents
Handles vector storage and retrieval
"""
from typing import List, Dict, Any, Optional
import uuid

import chromadb
from chromadb.config import Settings


class ChromaDBService:
    """Service for ChromaDB vector database operations"""

    def __init__(self, host: str = "localhost", port: int = 8000):
        self.client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=Settings(anonymized_telemetry=False),
        )

    @staticmethod
    def user_collection_name(user_id: str) -> str:
        """
        Collection-per-user naming.
        Prefix ensures valid collection name and avoids collisions.
        """
        return f"lda_u_{user_id}"

    def create_collection(self, collection_name: str, reset: bool = False):
        if reset:
            try:
                self.client.delete_collection(collection_name)
            except Exception:
                pass

        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        return collection

    def add_documents(
        self,
        collection_name: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ) -> int:
        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for chunk, embedding in zip(chunks, embeddings):
            chunk_id = chunk.get("chunk_id", str(uuid.uuid4()))
            ids.append(chunk_id)
            documents.append(chunk["text"])

            metadata = {
                "document_id": chunk.get("document_id", "unknown"),
                "chunk_index": chunk.get("chunk_index", 0),
                "word_count": chunk.get("word_count", 0),
                "char_count": chunk.get("char_count", 0),
            }
            if "metadata" in chunk and isinstance(chunk["metadata"], dict):
                metadata.update(chunk["metadata"])

            metadatas.append(metadata)

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        return len(ids)

    def query_collection(
        self,
        collection_name: str,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        collection = self.client.get_collection(collection_name)

        return collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

    def delete_where(self, collection_name: str, where: Dict[str, Any]) -> None:
        """
        Delete vectors by metadata filter (needed for doc delete / reprocess).
        """
        collection = self.client.get_collection(collection_name)
        collection.delete(where=where)

    def get_collection_count(self, collection_name: str) -> int:
        try:
            collection = self.client.get_collection(collection_name)
            return collection.count()
        except Exception:
            return 0

    def delete_collection(self, collection_name: str) -> bool:
        try:
            self.client.delete_collection(collection_name)
            return True
        except Exception:
            return False

    def list_collections(self) -> List[str]:
        collections = self.client.list_collections()
        return [c.name for c in collections]

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        try:
            collection = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "count": collection.count(),
                "metadata": collection.metadata,
            }
        except Exception as e:
            return {"name": collection_name, "count": 0, "error": str(e)}