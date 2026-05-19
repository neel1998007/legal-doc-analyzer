"""
RAG (Retrieval-Augmented Generation) Service
Orchestrates: extract -> chunk -> embed -> store -> retrieve
"""

from typing import Dict, Any, Optional

from app.services.extraction_service import ExtractionService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.chromadb_service import ChromaDBService


class RAGService:
    """Complete RAG pipeline service"""

    def __init__(
        self,
        chromadb_host: str = "localhost",
        chromadb_port: int = 8000,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100,
    ):
        """
        Defaults are production-oriented.
        For tests/small docs you can pass smaller chunk parameters.
        """
        self.extraction_service = ExtractionService()
        self.chunking_service = ChunkingService(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            min_chunk_size=min_chunk_size,
        )
        self.embedding_service = EmbeddingService()
        self.chromadb_service = ChromaDBService(host=chromadb_host, port=chromadb_port)

    def process_document(
        self,
        file_path: str,
        file_type: str,
        document_id: str,
        collection_name: str = "legal_documents",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        results: Dict[str, Any] = {
            "document_id": document_id,
            "success": False,
            "steps": {},
        }

        # Step 1: Extract text
        print(f"\n📄 Step 1: Extracting text from {file_path}")
        text = self.extraction_service.extract_text(file_path, file_type)

        results["steps"]["extraction"] = {
            "char_count": len(text),
            "word_count": len(text.split()),
        }

        if not text:
            results["error"] = "No text extracted from document"
            return results

        print(f"✅ Extracted {len(text)} characters")

        # Step 2: Chunk text
        print("\n✂️ Step 2: Chunking text")
        chunks = self.chunking_service.split_text(
            text=text,
            document_id=document_id,
            metadata=metadata or {},
        )

        results["steps"]["chunking"] = {
            "chunk_count": len(chunks),
            "stats": self.chunking_service.get_chunk_stats(chunks),
        }

        if not chunks:
            results["error"] = "No chunks created from document"
            return results

        print(f"✅ Created {len(chunks)} chunks")

        # Step 3: Generate embeddings
        print("\n🤖 Step 3: Generating embeddings")
        embedded_chunks = self.embedding_service.embed_chunks(chunks)

        results["steps"]["embedding"] = {
            "embedding_count": len(embedded_chunks),
            "dimension": embedded_chunks[0]["embedding_dimension"],
            "model": embedded_chunks[0]["embedding_model"],
        }

        print(f"✅ Generated {len(embedded_chunks)} embeddings")

        # Step 4: Store in ChromaDB
        print("\n💾 Step 4: Storing in ChromaDB")
        embeddings = [c["embedding"] for c in embedded_chunks]
        stored = self.chromadb_service.add_documents(
            collection_name=collection_name,
            chunks=embedded_chunks,
            embeddings=embeddings,
        )

        results["steps"]["storage"] = {
            "documents_stored": stored,
            "collection": collection_name,
        }

        print(f"✅ Stored {stored} documents in ChromaDB")

        results["success"] = True
        return results

    def query_documents(
        self,
        query: str,
        collection_name: str = "legal_documents",
        n_results: int = 5,
        document_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        print(f"\n🔍 Generating query embedding for: '{query}'")
        query_embedding = self.embedding_service.generate_embedding(query)

        where = {"document_id": document_id} if document_id else None

        print(f"🔍 Searching in collection: {collection_name}")
        results = self.chromadb_service.query_collection(
            collection_name=collection_name,
            query_embedding=query_embedding,
            n_results=n_results,
            where=where,
        )

        formatted = {"query": query, "results": []}

        if results and results.get("documents") and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                distance = results["distances"][0][i]
                formatted["results"].append(
                    {
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": distance,
                        "similarity": 1 - distance,
                    }
                )

        print(f"✅ Found {len(formatted['results'])} relevant chunks")
        return formatted

    def get_collection_info(self, collection_name: str = "legal_documents") -> Dict[str, Any]:
        return self.chromadb_service.get_collection_stats(collection_name)