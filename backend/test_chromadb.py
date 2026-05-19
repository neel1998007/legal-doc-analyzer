"""
Test ChromaDB integration and complete RAG pipeline
Run with: python test_chromadb.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.chromadb_service import ChromaDBService
from app.services.rag_service import RAGService

TEST_COLLECTION = "test_legal_docs"

def test_chromadb_connection():
    """Test 1: ChromaDB connection"""
    print("\n" + "="*50)
    print("🧪 TEST 1: ChromaDB Connection")
    print("="*50)

    try:
        service = ChromaDBService()
        collections = service.list_collections()
        print(f"✅ Connected to ChromaDB")
        print(f"📊 Existing collections: {collections}")
        return True
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return False

def test_collection_operations():
    """Test 2: Collection CRUD operations"""
    print("\n" + "="*50)
    print("🧪 TEST 2: Collection Operations")
    print("="*50)

    service = ChromaDBService()

    # Create collection
    collection = service.create_collection(TEST_COLLECTION, reset=True)
    print(f"✅ Created collection: {TEST_COLLECTION}")

    # Get count
    count = service.get_collection_count(TEST_COLLECTION)
    print(f"📊 Document count: {count} (should be 0)")

    return count == 0

def test_add_and_query():
    """Test 3: Add documents and query"""
    print("\n" + "="*50)
    print("🧪 TEST 3: Add & Query Documents")
    print("="*50)

    service = ChromaDBService()

    # Sample chunks with embeddings
    from app.services.embedding_service import EmbeddingService

    chunks = [
        {
            "chunk_id": "test_1",
            "document_id": "contract_001",
            "text": "Payment shall be made within 30 days of invoice receipt.",
            "chunk_index": 0,
            "word_count": 10,
            "metadata": {"type": "payment"}
        },
        {
            "chunk_id": "test_2",
            "document_id": "contract_001",
            "text": "Either party may terminate with 30 days written notice.",
            "chunk_index": 1,
            "word_count": 9,
            "metadata": {"type": "termination"}
        }
    ]

    # Generate embeddings
    embedded = EmbeddingService.embed_chunks(chunks)
    embeddings = [c["embedding"] for c in embedded]

    # Add to collection
    count = service.add_documents(TEST_COLLECTION, embedded, embeddings)
    print(f"✅ Added {count} documents")

    # Query
    query = "What are the payment terms?"
    query_emb = EmbeddingService.generate_embedding(query)

    results = service.query_collection(
        TEST_COLLECTION,
        query_emb,
        n_results=2
    )

    print(f"\n🔍 Query: '{query}'")
    print(f"📊 Results found: {len(results['documents'][0])}")

    if results['documents'][0]:
        print(f"\nTop result: {results['documents'][0][0][:100]}...")
        print(f"Distance: {results['distances'][0][0]:.4f}")

    return len(results['documents'][0]) > 0

def test_complete_rag_pipeline():
    """Test 4: Complete RAG pipeline with real document"""
    print("\n" + "="*50)
    print("🧪 TEST 4: Complete RAG Pipeline")
    print("="*50)

    # Check if test document exists
    docx_path = "./test_documents/test_contract.docx"

    if not os.path.exists(docx_path):
        print("⚠️ Test document not found, skipping")
        return True

    # Initialize RAG service
    rag = RAGService(
        chunk_size=50,
        chunk_overlap=10,
        min_chunk_size=10
    )

    # Process document
    print("\n📄 Processing complete document...")
    results = rag.process_document(
        file_path=docx_path,
        file_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        document_id="test_contract_full",
        collection_name=TEST_COLLECTION,
        metadata={"source": "test", "doc_type": "contract"}
    )

    if not results["success"]:
        print(f"❌ Processing failed: {results.get('error')}")
        return False

    print(f"\n✅ Processing complete!")
    print(f"📊 Steps:")
    for step, data in results["steps"].items():
        print(f"  - {step}: {data}")

    # Query the processed document
    print(f"\n🔍 Querying processed document...")
    query_results = rag.query_documents(
        query="What is this contract about?",
        collection_name=TEST_COLLECTION,
        n_results=3
    )

    print(f"\n📊 Query Results:")
    for i, result in enumerate(query_results["results"][:2]):
        print(f"\nResult {i+1} (similarity: {result['similarity']:.4f}):")
        print(f"  {result['text'][:150]}...")

    return len(query_results["results"]) > 0

def test_collection_stats():
    """Test 5: Collection statistics"""
    print("\n" + "="*50)
    print("🧪 TEST 5: Collection Statistics")
    print("="*50)

    service = ChromaDBService()
    stats = service.get_collection_stats(TEST_COLLECTION)

    print(f"📊 Collection: {stats['name']}")
    print(f"📊 Total documents: {stats['count']}")
    print(f"📊 Metadata: {stats.get('metadata', {})}")

    return stats["count"] > 0

def cleanup():
    """Cleanup test collection"""
    print("\n" + "="*50)
    print("🧹 Cleanup")
    print("="*50)

    service = ChromaDBService()
    service.delete_collection(TEST_COLLECTION)
    print(f"✅ Cleaned up test collection")

def main():
    """Main test function"""
    print("💾 Legal Document Analyzer - ChromaDB Integration Test")
    print("="*50)
    print("⚠️ Make sure ChromaDB is running on localhost:8000")

    tests_passed = 0
    total_tests = 5

    if test_chromadb_connection():
        tests_passed += 1

    if test_collection_operations():
        tests_passed += 1

    if test_add_and_query():
        tests_passed += 1

    if test_complete_rag_pipeline():
        tests_passed += 1

    if test_collection_stats():
        tests_passed += 1

    # Cleanup
    cleanup()

    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    print(f"✅ Tests passed: {tests_passed}/{total_tests}")

    if tests_passed == total_tests:
        print("🎉 All tests passed! RAG pipeline is working!")
    else:
        print("⚠️ Some tests failed. Check errors above.")

if __name__ == "__main__":
    main()