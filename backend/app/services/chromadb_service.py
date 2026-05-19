"""
ChromaDB Service for Legal Documents
Handles vector storage and retrieval
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import uuid


class ChromaDBService:
    """Service for ChromaDB vector database operations"""

    def __init__(self, host: str = "localhost", port: int = 8000):
        """
        Initialize ChromaDB client

        Args:
            host: ChromaDB host
            port: ChromaDB port
        """
        self.client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        print(f"✅ Connected to ChromaDB at {host}:{port}")

    def create_collection(
        self,
        collection_name: str,
        reset: bool = False
    ):
        """
        Create or get a collection

        Args:
            collection_name: Name of the collection
            reset: If True, delete existing collection first

        Returns:
            ChromaDB collection object
        """
        if reset:
            try:
                self.client.delete_collection(collection_name)
                print(f"🗑️ Deleted existing collection: {collection_name}")
            except Exception:
                pass

        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        print(f"✅ Collection ready: {collection_name}")
        return collection

    def add_documents(
        self,
        collection_name: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> int:
        """
        Add document chunks with embeddings to collection

        Args:
            collection_name: Name of the collection
            chunks: List of chunk dictionaries
            embeddings: List of embedding vectors

        Returns:
            Number of documents added
        """
        collection = self.client.get_or_create_collection(collection_name)

        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []

        for chunk, embedding in zip(chunks, embeddings):
            # Generate unique ID
            chunk_id = chunk.get("chunk_id", str(uuid.uuid4()))
            ids.append(chunk_id)

            # Store text
            documents.append(chunk["text"])

            # Store metadata
            metadata = {
                "document_id": chunk.get("document_id", "unknown"),
                "chunk_index": chunk.get("chunk_index", 0),
                "word_count": chunk.get("word_count", 0),
                "char_count": chunk.get("char_count", 0),
            }
            # Add any additional metadata
            if "metadata" in chunk:
                metadata.update(chunk["metadata"])

            metadatas.append(metadata)

        # Add to ChromaDB
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

        print(f"✅ Added {len(ids)} documents to {collection_name}")
        return len(ids)

    def query_collection(
        self,
        collection_name: str,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Query collection for similar documents

        Args:
            collection_name: Name of the collection
            query_embedding: Query vector
            n_results: Number of results to return
            where: Metadata filter (optional)

        Returns:
            Query results with documents and metadata
        """
        collection = self.client.get_collection(collection_name)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"]
        )

        return results

    def get_collection_count(self, collection_name: str) -> int:
        """Get number of documents in collection"""
        try:
            collection = self.client.get_collection(collection_name)
            return collection.count()
        except Exception:
            return 0

    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection"""
        try:
            self.client.delete_collection(collection_name)
            print(f"🗑️ Deleted collection: {collection_name}")
            return True
        except Exception as e:
            print(f"❌ Error deleting collection: {e}")
            return False

    def list_collections(self) -> List[str]:
        """List all collections"""
        collections = self.client.list_collections()
        return [c.name for c in collections]

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics about a collection"""
        try:
            collection = self.client.get_collection(collection_name)
            count = collection.count()

            # Get a sample to check metadata
            sample = collection.peek(limit=1)

            return {
                "name": collection_name,
                "count": count,
                "metadata": collection.metadata,
                "sample_available": len(sample["ids"]) > 0
            }
        except Exception as e:
            return {
                "name": collection_name,
                "count": 0,
                "error": str(e)
            }